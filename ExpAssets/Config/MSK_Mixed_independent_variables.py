from klibs.KLIndependentVariable import IndependentVariableSet

MSK_Mixed_ind_vars = IndependentVariableSet()

MSK_Mixed_ind_vars.add_variable('isoa', int, [100,200,300])
MSK_Mixed_ind_vars.add_variable('ttoa', int, [120,240,360,480,600])
MSK_Mixed_ind_vars.add_variable('t1_difficulty', str, ['easy', 'medium', 'hard'])