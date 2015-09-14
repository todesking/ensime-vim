execute 'pyfile' expand('<sfile>:p').'.py'

function! ensime#function_en_complete_func(arg0, arg1) abort
    return s:call_plugin('function_en_complete_func', [a:arg0, a:arg1])
endfunction

function! ensime#autocmd_vim_leave(arg0, arg1) abort
    return s:call_plugin('autocmd_vim_leave', [a:arg0, a:arg1])
endfunction

function! ensime#autocmd_buf_write_post(arg0, arg1) abort
    return s:call_plugin('autocmd_buf_write_post', [a:arg0, a:arg1])
endfunction

function! ensime#autocmd_cursor_hold(arg0, arg1) abort
    return s:call_plugin('autocmd_cursor_hold', [a:arg0, a:arg1])
endfunction

function! ensime#autocmd_cursor_moved(arg0, arg1) abort
    return s:call_plugin('autocmd_cursor_moved', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_no_teardown(arg0, arg1) abort
    return s:call_plugin('command_en_no_teardown', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_type_check(arg0, arg1) abort
    return s:call_plugin('command_en_type_check', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_type(arg0, arg1) abort
    return s:call_plugin('command_en_type', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_declaration(arg0, arg1) abort
    return s:call_plugin('command_en_declaration', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_symbol(arg0, arg1) abort
    return s:call_plugin('command_en_symbol', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_doc_uri(arg0, arg1) abort
    return s:call_plugin('command_en_doc_uri', [a:arg0, a:arg1])
endfunction

function! ensime#command_en_doc_browse(arg0, arg1) abort
    return s:call_plugin('command_en_doc_browse', [a:arg0, a:arg1])
endfunction

function! s:call_plugin(method_name, args) abort
    unlet! g:__error
    python <<PY
try:
  r = getattr(ensime_plugin, vim.eval('a:method_name'))(vim.eval('a:args'))
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
