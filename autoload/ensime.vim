execute 'pyfile' expand('<sfile>:p').'.py'

function! ensime#teardown_all() abort
    return s:call_plugin('teardown_all', [])
endfunction

function! ensime#current_client() abort
    return s:call_plugin('current_client', [])
endfunction

function! ensime#client_for(config_path) abort
    return s:call_plugin('client_for', [a:config_path])
endfunction

function! ensime#find_config_path(path) abort
    return s:call_plugin('find_config_path', [a:path])
endfunction

function! ensime#with_current_client(proc) abort
    return s:call_plugin('with_current_client', [a:proc])
endfunction

function! ensime#current_offset_range() abort
    return s:call_plugin('current_offset_range', [])
endfunction

function! ensime#update() abort
    return s:call_plugin('update', [])
endfunction

function! ensime#function_en_complete_func(args) abort
    return s:call_plugin('function_en_complete_func', [a:args])
endfunction

function! ensime#autocmd_vim_leave(_) abort
    return s:call_plugin('autocmd_vim_leave', [a:_])
endfunction

function! ensime#autocmd_buf_write_post(_) abort
    return s:call_plugin('autocmd_buf_write_post', [a:_])
endfunction

function! ensime#autocmd_cursor_hold(_) abort
    return s:call_plugin('autocmd_cursor_hold', [a:_])
endfunction

function! ensime#autocmd_cursor_moved(_) abort
    return s:call_plugin('autocmd_cursor_moved', [a:_])
endfunction

function! ensime#command_en_no_teardown(_) abort
    return s:call_plugin('command_en_no_teardown', [a:_])
endfunction

function! ensime#command_en_type_check(_) abort
    return s:call_plugin('command_en_type_check', [a:_])
endfunction

function! ensime#command_en_type(_) abort
    return s:call_plugin('command_en_type', [a:_])
endfunction

function! ensime#command_en_declaration(_) abort
    return s:call_plugin('command_en_declaration', [a:_])
endfunction

function! ensime#command_en_symbol(_) abort
    return s:call_plugin('command_en_symbol', [a:_])
endfunction

function! ensime#command_en_doc_uri(_) abort
    return s:call_plugin('command_en_doc_uri', [a:_])
endfunction

function! ensime#command_en_doc_browse(_) abort
    return s:call_plugin('command_en_doc_browse', [a:_])
endfunction

function! s:call_plugin(method_name, args) abort
    " TODO: support nvim rpc
    if has('nvim')
      throw 'Call rplugin from vimscript: not supported yet'
    endif
    unlet! g:__error
    python <<PY
try:
  r = getattr(ensime_plugin, vim.eval('a:method_name'))(*vim.eval('a:args'))
  vim.command('let g:__result = ' + json.dumps(([] if r == None else r)))
except:
  vim.command('let g:__error = ' + json.dumps(str(sys.exc_info()[0]) + ':' + str(sys.exc_info()[1])))
PY
    if exists('g:__error')
      throw g:__error
    endif
    let res = g:__result
    unlet g:__result
    return res
endfunction
