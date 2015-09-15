if has('nvim')
  finish
endif
augroup ensime
    autocmd!
    autocmd VimLeave * call ensime#autocmd_vim_leave('', '')
    autocmd BufWritePost * call ensime#autocmd_buf_write_post('', '')
    autocmd CursorHold * call ensime#autocmd_cursor_hold('', '')
    autocmd CursorMoved * call ensime#autocmd_cursor_moved('', '')
augroup END

command! -nargs=0 EnNoTeardown call ensime#command_en_no_teardown('', '')
command! -nargs=0 EnTypeCheck call ensime#command_en_type_check('', '')
command! -nargs=0 EnType call ensime#command_en_type('', '')
command! -nargs=0 EnDeclaration call ensime#command_en_declaration('', '')
command! -nargs=0 EnSymbol call ensime#command_en_symbol('', '')
command! -nargs=0 EnDocUri call ensime#command_en_doc_uri('', '')
command! -nargs=0 EnDocBrowse call ensime#command_en_doc_browse('', '')

function! EnCompleteFunc(arg1, arg2) abort
    return ensime#function_en_complete_func(a:arg1, a:arg2)
endfunction
