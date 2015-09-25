if !has('nvim')
    execute 'pyfile' expand('<sfile>:p').'.py'
endif

function! ensime#auto_start_enabled() abort
    return s:call_plugin('auto_start_enabled', [])
endfunction

function! ensime#client_keys() abort
    return s:call_plugin('client_keys', [])
endfunction

function! ensime#client_status(config_path) abort
    return s:call_plugin('client_status', [a:config_path])
endfunction

function! ensime#teardown() abort
    return s:call_plugin('teardown', [])
endfunction

function! ensime#current_client() abort
    return s:call_plugin('current_client', [])
endfunction

function! ensime#client_for(config_path, create) abort
    return s:call_plugin('client_for', [a:config_path, a:create])
endfunction

function! ensime#current_config_path() abort
    return s:call_plugin('current_config_path', [])
endfunction

function! ensime#find_config_path(path) abort
    return s:call_plugin('find_config_path', [a:path])
endfunction

function! ensime#with_current_client(proc, warn_if_unavailable) abort
    return s:call_plugin('with_current_client', [a:proc, a:warn_if_unavailable])
endfunction

function! ensime#fun_en_complete_func(args) abort
    return s:call_plugin('fun_en_complete_func', [a:args])
endfunction

function! ensime#au_vimleave(filename) abort
    return s:call_plugin('au_vimleave', [a:filename])
endfunction

function! ensime#au_buf_write_post(filename) abort
    return s:call_plugin('au_buf_write_post', [a:filename])
endfunction

function! ensime#au_cursor_hold(filename) abort
    return s:call_plugin('au_cursor_hold', [a:filename])
endfunction

function! ensime#au_cursor_moved(filename) abort
    return s:call_plugin('au_cursor_moved', [a:filename])
endfunction

function! ensime#com_en_start(args, range) abort
    return s:call_plugin('com_en_start', [a:args, a:range])
endfunction

function! ensime#com_en_no_teardown(args, range) abort
    return s:call_plugin('com_en_no_teardown', [a:args, a:range])
endfunction

function! ensime#com_en_type_check(args, range) abort
    return s:call_plugin('com_en_type_check', [a:args, a:range])
endfunction

function! ensime#com_en_type(args, range) abort
    return s:call_plugin('com_en_type', [a:args, a:range])
endfunction

function! ensime#com_en_declaration(args, range) abort
    return s:call_plugin('com_en_declaration', [a:args, a:range])
endfunction

function! ensime#com_en_symbol(args, range) abort
    return s:call_plugin('com_en_symbol', [a:args, a:range])
endfunction

function! ensime#com_en_doc_uri(args, range) abort
    return s:call_plugin('com_en_doc_uri', [a:args, a:range])
endfunction

function! ensime#com_en_doc_browse(args, range) abort
    return s:call_plugin('com_en_doc_browse', [a:args, a:range])
endfunction

function! ensime#com_en_clients(args, range) abort
    return s:call_plugin('com_en_clients', [a:args, a:range])
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
