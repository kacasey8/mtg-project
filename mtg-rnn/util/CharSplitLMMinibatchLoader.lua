-- like memcpy; write t2 into t1, but quickly
function tencpy(t1, t2)
   local n = t2:size(1)
   local t1_sub = t1:sub(1, n)
   t1_sub:copy(t2)
end
-- only write the first n characters of t2, exactly like memcpy
function tencpy(t1, t2, n)
   local t1_sub = t1:sub(1, n)
   local t2_sub = t2:sub(1, n)
   t1_sub:copy(t2_sub)
end
-- specify an offset into both tensors
function tencpy(t1, t1i, t2, t2i, n)
   local t1_sub = t1:sub(t1i, t1i + n - 1)
   local t2_sub = t2:sub(t2i, t2i + n - 1)
   t1_sub:copy(t2_sub)
end

-- Modified from https://github.com/oxford-cs-ml-2015/practical6
-- the modification included support for train/val/test splits

local CharSplitLMMinibatchLoader = {}
CharSplitLMMinibatchLoader.__index = CharSplitLMMinibatchLoader

function CharSplitLMMinibatchLoader.create(data_dir, batch_size, seq_length, 
					   max_epochs, split_fractions, rmana, rfields)
    -- split_fractions is e.g. {0.9, 0.05, 0.05}

    local self = {}
    setmetatable(self, CharSplitLMMinibatchLoader)

    local input_file = path.join(data_dir, 'input.txt')
    local vocab_file = path.join(data_dir, 'vocab.t7')
    local tensor_file = path.join(data_dir, 'data.t7')

    -- fetch file attributes to determine if we need to rerun preprocessing
    local run_prepro = false
    if not (path.exists(vocab_file) or path.exists(tensor_file)) then
        -- prepro files do not exist, generate them
        print('vocab.t7 and data.t7 do not exist. Running preprocessing...')
        run_prepro = true
    else
        -- check if the input file was modified since last time we 
        -- ran the prepro. if so, we have to rerun the preprocessing
        local input_attr = lfs.attributes(input_file)
        local vocab_attr = lfs.attributes(vocab_file)
        local tensor_attr = lfs.attributes(tensor_file)
        if input_attr.modification > vocab_attr.modification or input_attr.modification > tensor_attr.modification then
            print('vocab.t7 or data.t7 detected as stale. Re-running preprocessing...')
            run_prepro = true
        end
    end
    if run_prepro then
        -- construct a tensor with all the data, and vocab file
        print('one-time setup: preprocessing input text file ' .. input_file .. '...')
        CharSplitLMMinibatchLoader.text_to_tensor(input_file, vocab_file, tensor_file)
    end

    print('loading data files...')
    local data = torch.load(tensor_file)
    self.vocab_mapping = torch.load(vocab_file)

    --------
    -- perform safety checks on split_fractions, exactly the same as below
    assert(split_fractions[1] >= 0 and split_fractions[1] <= 1, 'bad split fraction ' .. split_fractions[1] .. ' for train, not between 0 and 1')
    assert(split_fractions[2] >= 0 and split_fractions[2] <= 1, 'bad split fraction ' .. split_fractions[2] .. ' for val, not between 0 and 1')
    assert(split_fractions[3] >= 0 and split_fractions[3] <= 1, 'bad split fraction ' .. split_fractions[3] .. ' for test, not between 0 and 1')

    -- this check is actually new
    local epsilon = 0.0001
    assert(1.0 - epsilon < split_fractions[1] + split_fractions[2] + split_fractions[3]
	      and split_fractions[1] + split_fractions[2] + split_fractions[3] < 1.0 + epsilon)

    -- do all preprocessing work here; might modify split_fractions as well
    data = CharSplitLMMinibatchLoader.process_cards(data, self.vocab_mapping, max_epochs, 
						    batch_size, seq_length, split_fractions,
						    rmana, rfields)
    --------

    -- cut off the end so that it divides evenly
    local len = data:size(1)
    if len % (batch_size * seq_length) ~= 0 then
        print('cutting off end of data so that the batches/sequences divide evenly')
        data = data:sub(1, batch_size * seq_length 
                    * math.floor(len / (batch_size * seq_length)))
    end

    -- count vocab
    self.vocab_size = 0
    for _ in pairs(self.vocab_mapping) do 
        self.vocab_size = self.vocab_size + 1 
    end

    -- self.batches is a table of tensors
    print('reshaping tensor...')
    self.batch_size = batch_size
    self.seq_length = seq_length

    local ydata = data:clone()
    ydata:sub(1,-2):copy(data:sub(2,-1))
    ydata[-1] = data[1]
    self.x_batches = data:view(batch_size, -1):split(seq_length, 2)  -- #rows = #batches
    self.nbatches = #self.x_batches
    self.y_batches = ydata:view(batch_size, -1):split(seq_length, 2)  -- #rows = #batches
    assert(#self.x_batches == #self.y_batches)

    -- lets try to be helpful here
    if self.nbatches < 50 then
        print('WARNING: less than 50 batches in the data in total? Looks like very small dataset. You probably want to use smaller batch_size and/or seq_length.')
    end

    -- duplicate check, as fractions might have changed during preprocessing
    assert(split_fractions[1] >= 0 and split_fractions[1] <= 1, 'bad split fraction ' .. split_fractions[1] .. ' for train, not between 0 and 1')
    assert(split_fractions[2] >= 0 and split_fractions[2] <= 1, 'bad split fraction ' .. split_fractions[2] .. ' for val, not between 0 and 1')
    assert(split_fractions[3] >= 0 and split_fractions[3] <= 1, 'bad split fraction ' .. split_fractions[3] .. ' for test, not between 0 and 1')
    if split_fractions[3] == 0 then 
        -- catch a common special case where the user might not want a test set
        self.ntrain = math.floor(self.nbatches * split_fractions[1])
        self.nval = self.nbatches - self.ntrain
        self.ntest = 0
    else
        -- divide data to train/val and allocate rest to test
        self.ntrain = math.floor(self.nbatches * split_fractions[1])
        self.nval = math.floor(self.nbatches * split_fractions[2])
        self.ntest = self.nbatches - self.nval - self.ntrain -- the rest goes to test (to ensure this adds up exactly)
    end

    self.split_sizes = {self.ntrain, self.nval, self.ntest}
    self.batch_ix = {0,0,0}

    print(string.format('data load done. Number of data batches in train: %d, val: %d, test: %d', self.ntrain, self.nval, self.ntest))
    collectgarbage()
    return self
end

function CharSplitLMMinibatchLoader:reset_batch_pointer(split_index, batch_index)
    batch_index = batch_index or 0
    self.batch_ix[split_index] = batch_index
end

function CharSplitLMMinibatchLoader:next_batch(split_index)
    if self.split_sizes[split_index] == 0 then
        -- perform a check here to make sure the user isn't screwing something up
        local split_names = {'train', 'val', 'test'}
        print('ERROR. Code requested a batch for split ' .. split_names[split_index] .. ', but this split has no data.')
        os.exit() -- crash violently
    end
    -- split_index is integer: 1 = train, 2 = val, 3 = test
    self.batch_ix[split_index] = self.batch_ix[split_index] + 1
    if self.batch_ix[split_index] > self.split_sizes[split_index] then
        self.batch_ix[split_index] = 1 -- cycle around to beginning
    end
    -- pull out the correct next batch
    local ix = self.batch_ix[split_index]
    if split_index == 2 then ix = ix + self.ntrain end -- offset by train set size
    if split_index == 3 then ix = ix + self.ntrain + self.nval end -- offset by train + val
    return self.x_batches[ix], self.y_batches[ix]
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.text_to_tensor(in_textfile, out_vocabfile, out_tensorfile)
    local timer = torch.Timer()

    print('loading text file...')
    local cache_len = 10000
    local rawdata
    local tot_len = 0
    local f = assert(io.open(in_textfile, "r"))

    -- create vocabulary if it doesn't exist yet
    print('creating vocabulary mapping...')
    -- record all characters to a set
    local unordered = {}
    rawdata = f:read(cache_len)
    repeat
        for char in rawdata:gmatch'.' do
            if not unordered[char] then unordered[char] = true end
        end
        tot_len = tot_len + #rawdata
        rawdata = f:read(cache_len)
    until not rawdata
    f:close()
    -- sort into a table (i.e. keys become 1..N)
    local ordered = {}
    for char in pairs(unordered) do ordered[#ordered + 1] = char end
    table.sort(ordered)
    -- invert `ordered` to create the char->int mapping
    local vocab_mapping = {}
    for i, char in ipairs(ordered) do
        vocab_mapping[char] = i
    end
    -- construct a tensor with all the data
    print('putting data into tensor...')
    local data = torch.ByteTensor(tot_len) -- store it into 1D first, then rearrange
    f = assert(io.open(in_textfile, "r"))
    local currlen = 0
    rawdata = f:read(cache_len)
    repeat
        for i=1, #rawdata do
            data[currlen+i] = vocab_mapping[rawdata:sub(i, i)] -- lua has no string indexing using []
        end
        currlen = currlen + #rawdata
        rawdata = f:read(cache_len)
    until not rawdata
    f:close()

    -- save output preprocessed files
    print('saving ' .. out_vocabfile)
    torch.save(out_vocabfile, vocab_mapping)
    print('saving ' .. out_tensorfile)
    torch.save(out_tensorfile, data)
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.process_cards(data, vocab_mapping, max_epochs, 
						  batch_size, seq_length, split_fractions,
						  rmana, rfields)
    -- split_fractions is e.g. {0.9, 0.05, 0.05}
   math.randomseed(torch.random())

   print('\n-- preprocessing MTG cards --')
   if rmana then print('  randomizing mana costs') end
   if rfields then print('  randomizing field ordering') end

   local datalen = data:size(1)
   local split_val_test = split_fractions[2] + split_fractions[3]
   local split_val_effective = split_fractions[2] / split_val_test

   local est_batches = math.floor(datalen / (batch_size * seq_length))
   local est_batches_train = math.floor(est_batches * split_fractions[1])
   local est_batches_nontrain = est_batches - est_batches_train

   local batches_train = est_batches_train * max_epochs
   local batches_val = math.floor(est_batches_nontrain * split_val_effective)
   local batches_test = est_batches_nontrain - batches_val
   local batches_total = batches_train + batches_val + batches_test
   local final_datalen = batches_total * batch_size * seq_length
   
   print('dataset is ' .. datalen .. ' characters:')
   print('  ' .. est_batches .. ' batches, each batch is ' 
	    .. seq_length .. ' long by ' .. batch_size .. ' wide')
   print('  ' .. batches_total .. ' total batches over ' .. max_epochs .. ' training epochs')
   print('  training batches: ' .. est_batches_train .. ' * ' .. max_epochs 
	    .. ' = ' .. batches_train)
   print('  validation batches: ' .. batches_val)
   print('  test batches: ' .. batches_test)

   -- sanity
   if batches_train < 1 then
      print('ERROR: no training batches')
      print('  Training will not be possible with this configuration.')
      os.exit()
   end
   
   local ivocab = {}
   for c,i in pairs(vocab_mapping) do ivocab[i] = c end

   -- Separator settings: lookups will return nil if the characters don't exist in the vocab,
   -- which is fine.
   local newline = vocab_mapping['\n']
   local fieldsep = vocab_mapping['|']
   local msymstart = vocab_mapping['{']
   local msymend = vocab_mapping['}']
   local mcounter = vocab_mapping['^']

   -- Try to separate the dataset into cards; fail and return the original dataset if we can't.
   local cards = {}

   local next_card_start = 1
   local data_idx = 1
   local card_idx = 1
   local anomaly_multiple_newlines = false
   data:apply(function(e)
	 -- If there isn't a double newline after the last card, we'll miss it.
	 -- Also, sequences of more than 2 newlines will break everything.
	 if e == newline and data_idx < datalen and data[data_idx + 1] == newline then
	    -- double newline is included on the end of the card
	    cards[card_idx] = data:sub(next_card_start, data_idx + 1)
	    card_idx = card_idx + 1
	    -- set the next card start; fine if this goes oob, as we won't be able to use it
	    next_card_start = data_idx + 2
	    -- check for issues that will make the data meaningless
	    if data_idx + 1 < datalen and data[data_idx + 2] == newline then
	       anomaly_multiple_newlines = true
	    end
	 end
	 -- increment data index
	 data_idx = data_idx + 1
	 --print(data_idx .. ': ' .. e)
   end)

   local cards_total = card_idx - 1

   -- sanity checks
   if anomaly_multiple_newlines then
      print('ERROR: found a sequence of 3 or more consecutive newlines.')
      print('  This confuses the process of separating cards.')
      os.exit()
   end
   if cards_total <= 1 then
      print('ERROR: only found one thing that looks like a card.')
      print('  It makes no sense to proceed.')
      os.exit()
   end

   local cards_train = math.floor(cards_total * split_fractions[1])
   local cards_nontrain = cards_total - cards_train
   local cards_val = math.floor(cards_nontrain * split_val_effective)
   local cards_test = cards_nontrain - cards_val
   assert(cards_train <= cards_total, 'too many training cards: ' 
	     .. cards_train .. ' (training) > ' .. cards_total .. ' (total)')
   assert(cards_train + cards_val <= cards_total, 'too many training and validation cards: ' 
	     .. cards_train .. ' (training) + ' .. cards_val .. ' (validation) > ' .. cards_total 
	     .. ' (total)')
   assert(cards_train + cards_val + cards_test == cards_total, 'card counts do not match: ' 
	     .. cards_train .. ' (training) + ' .. cards_val .. ' (validation) + ' 
	     .. cards_val .. ' (test) ~= ' .. cards_total .. ' (total)')

   print('found ' .. cards_total .. ' cards:')
   print('  using ' .. cards_train .. ' for training (' .. split_fractions[1] .. ')')
   print('  using ' .. cards_val .. ' for validation (' .. split_fractions[2] .. ')')
   print('  using ' .. cards_test .. ' for testing (' .. split_fractions[3] .. ')')

   -- reassign split fractions
   split_fractions[1] = batches_train / batches_total
   split_fractions[2] = batches_val / batches_total
   split_fractions[3] = batches_test / batches_total
   print('reassigned split fractions based on new batch counts:')
   print('  fraction training batches: ' .. split_fractions[1])
   print('  fraction validation batches: ' .. split_fractions[2])
   print('  fraction test batches: ' .. split_fractions[3])

   -- check the number of batches the loader will see after preprocessing
   local final_batches = math.floor(final_datalen / (batch_size * seq_length))
   if final_datalen % (batch_size * seq_length) ~= 0 then
      print('ROUNDING ERROR: ' .. final_datalen .. '(' .. actual_batches .. ' * '
	       .. batch_size * seq_length .. ') % ' .. batch_size * seq_length .. ' == '
	       .. final_datalen % (batch_size * seq_length) .. ' ~= 0')
   end

   local ntrain = 0
   local nval = 0
   local ntest = 0
   ---- duplicated logic from CharSplitLMMinibatchLoader.create ----
   if split_fractions[3] == 0 then 
      -- catch a common special case where the user might not want a test set
      ntrain = math.floor(final_batches * split_fractions[1])
      nval = final_batches - ntrain
      ntest = 0
   else
      -- divide data to train/val and allocate rest to test
      ntrain = math.floor(final_batches * split_fractions[1])
      nval = math.floor(final_batches * split_fractions[2])
      ntest = final_batches - nval - ntrain -- the rest goes to test (to ensure this adds up exactly)
   end
   ---- end duplicated logic ----
   local ctrain = ntrain * batch_size * seq_length
   local cval = nval * batch_size * seq_length
   local ctest = ntest * batch_size * seq_length
   assert(ctrain <= final_datalen, 'training set too large: ' 
	     .. ctrain .. ' (training) > ' .. final_datalen .. ' (full data set size)')
   assert(ctrain + cval <= final_datalen, 'training or validation set too large: ' 
	     .. ctrain .. ' (training) + ' .. cval .. ' (validation) > ' .. final_datalen 
	     .. ' (full data set size)')
   assert(ctrain + cval + ctest == final_datalen, 'split sizes do not match: ' 
	     .. ctrain .. ' (training) + ' .. cval .. ' (validation) + ' .. cval .. ' (test) ~= '
	     .. final_datalen .. ' (full data set size)')
   
   print('rewriting data into '.. final_batches .. ' batches, counts should be the same as above:')
   print('  ' .. ntrain .. ' training batches (' .. ctrain .. ' characters)')
   print('  ' .. nval .. ' validation batches (' .. cval .. ' characters)')
   print('  ' .. ntest .. ' test batches (' .. ctest .. ' characters)')

   local newdata = torch.ByteTensor(final_datalen)

   local newdata_train = newdata:sub(1, ctrain)
   local cardsplit_train = {}
   for i = 1,cards_train do cardsplit_train[i] = cards[i] end
   print('writing training data:')
   CharSplitLMMinibatchLoader.write_cardset(newdata_train, cardsplit_train, cards_train, 
					    rmana, rfields, 
					    newline, fieldsep, msymstart, msymend, mcounter)

   local newdata_val = nil
   local cardsplit_val = {}
   if cval > 0 then
      newdata_val = newdata:sub(ctrain + 1, ctrain + cval)
      for i = 1,cards_val do cardsplit_val[i] = cards[i + cards_train] end
      print('writing validation data:')
      CharSplitLMMinibatchLoader.write_cardset(newdata_val, cardsplit_val, cards_val, 
					       rmana, rfields, 
					       newline, fieldsep, msymstart, msymend, mcounter)
   end

   local newdata_test = nil
   local cardsplit_test = {}
   if ctest > 0 then
      newdata_test = newdata:sub(ctrain + cval + 1, ctrain + cval + ctest)
      for i = 1,cards_test do cardsplit_test[i] = cards[i + cards_train + cards_val] end
      print('writing test data:')
      CharSplitLMMinibatchLoader.write_cardset(newdata_test, cardsplit_test, cards_test, 
					       rmana, rfields, 
					       newline, fieldsep, msymstart, msymend, mcounter)
   end

   --CharSplitLMMinibatchLoader.data_dump(newdata, seq_length * batch_size, ivocab)
   --CharSplitLMMinibatchLoader.data_dump(newdata, 0, ivocab)

   print '-- done preprocessing MTG cards --\n'

   return newdata
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.write_cardset(data, cards, cardcount, rmana, rfields, 
						  newline, fieldsep, 
						  msymstart, msymend, mcounter)
   local idx = 1
   local z = nil
   local z_idx = cardcount + 1
   -- bookkeeping
   local count_loops = 0
   local count_cards = 0
   while idx <= data:size(1) do
      if z_idx > cardcount then
	 z = CharSplitLMMinibatchLoader.random_permutation(cardcount)
	 z_idx = 1
	 count_loops = count_loops + 1
      end
      idx = idx + CharSplitLMMinibatchLoader.write_card(data, idx, cards[z[z_idx]], rmana, rfields,
							newline, fieldsep, 
							msymstart, msymend, mcounter)
      z_idx = z_idx + 1
      count_cards = count_cards + 1
   end
   print('  looped ' .. count_loops .. ' times over ' .. cardcount .. ' cards for ' 
	    .. count_cards .. ' total')
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.write_card(data, data_idx, card, rmana, rfields,
					       newline, fieldsep, 
					       msymstart, msymend, mcounter)
   local newcard = card
   if rfields then
      local cardsize = card:size(1)
      local fields = {}
      local terminal = nil

      local field_start = 1
      local field_idx = 1
      local i = 1
      local fields_not_done = true
      card:apply(function(e)
	    if (e == fieldsep or e == newline) and i > field_start and fields_not_done then
	       -- include fieldsep at beginning of field, but not at end
	       fields[field_idx] = card:sub(field_start, i-1)
	       field_idx = field_idx + 1
	       field_start = i
	       -- special case to leave a final fieldsep in the terminal
	       if e == newline or (i < cardsize and card[i + 1] == newline) then
		  fields_not_done = false
	       end
	    end
	    i = i + 1
      end)

      newcard = torch.ByteTensor(cardsize)

      local fieldcount = field_idx - 1
      local z = CharSplitLMMinibatchLoader.random_permutation(fieldcount)
      i = 1
      for z_idx = 1,fieldcount do
	 local field = fields[z[z_idx]]
	 local len = field:size(1)
	 tencpy(newcard, i, field, 1, len)
	 i = i + len
      end
      
      -- deal with newlines on end of card, which under normal circumstances we should see
      if fields_not_done then
	 print('WARNING: no newline on end of card!')
      end
      terminal = card:sub(field_start, cardsize)
      tencpy(newcard, i, terminal, 1, terminal:size(1))
   end

   local to_write = data:size(1) - data_idx + 1
   if newcard:size(1) < to_write then
      to_write = newcard:size(1)
   end
   tencpy(data, data_idx, newcard, 1, to_write)

   if rmana then
      local cardview = data:sub(data_idx, data_idx + to_write - 1)
      local start_idx = 0
      local i = 1
      cardview:apply(function(e)
	    if e == msymstart then
	       start_idx = i
	    elseif e == msymend and start_idx > 0  and i - start_idx > 1 then
	       CharSplitLMMinibatchLoader.rewrite_mana(cardview, start_idx + 1,
						       newcard, start_idx + 1,
						       i - start_idx - 1, mcounter)
	       start_idx = 0
	    end
	    i = i + 1
      end)
   end
   
   return to_write
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.rewrite_mana(data, data_idx, card, card_idx, len, mcounter)
   local data_cost = data:sub(data_idx, data_idx + len - 1)
   local card_cost = card:sub(card_idx, card_idx + len - 1)
   local syms = {}

   local sym_idx = 1
   local sym_first_char = true
   local i = 1
   -- no checking or anything; this will break if the cost isn't correctly formatted
   card_cost:apply(function(e)
	 if e ~= mcounter and sym_first_char then
	    syms[sym_idx] = card_cost:sub(i, i + 1)
	    sym_idx = sym_idx + 1
	    sym_first_char = false
	 else
	    if e == mcounter then
	       syms[sym_idx] = card_cost:sub(i, i)
	       sym_idx = sym_idx + 1
	    end
	    sym_first_char = true
	 end
	 i = i + 1
   end)

   local z = CharSplitLMMinibatchLoader.random_permutation(sym_idx - 1)

   sym_idx = 1
   sym_first_char = true
   i = 1
   -- mutate the data, while leaving our sources in the card untouched
   data_cost:apply(function(e)
	 if sym_first_char then
	    local sym = syms[z[sym_idx]]
	    sym_idx = sym_idx + 1
	    local n = sym:size(1)
	    tencpy(data_cost, i, sym, 1, n)
	    if n > 1 then
	       sym_first_char = false
	    end
	 else
	    sym_first_char = true
	 end
	 i = i + 1
   end)
end

-- *** STATIC method ***
function CharSplitLMMinibatchLoader.data_dump(data, batchsize, ivocab)
   print('====================')
   local i = 1
   data:apply(function(e)
	 if batchsize > 0 and 1 < i and i < data:size(1) and i % batchsize == 1 then
	    print('\n--------------------')
	 end
	 i = i + 1
	 io.write(ivocab[e])
   end)
   print('\n====================')
end
	 
-- *** STATIC method ***
function CharSplitLMMinibatchLoader.random_permutation(n)
   -- a simple knuth shuffle
   local z = torch.IntTensor(n)
   for i = 1,z:size(1) do
      z[i] = i
   end
   for i = 1,z:size(1) do
      local r = math.random(z:size(1))
      local tmp = z[i]
      z[i] = z[r]
      z[r] = tmp
   end
   return z
end

return CharSplitLMMinibatchLoader
