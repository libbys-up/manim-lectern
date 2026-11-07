==== Pushing a value
mips code
li    $t0, 7
addiu $sp, $sp, -4
sw    $t0, 0($sp)
-- left --
registers $t0 and the stack on the right, $sp at 0x8000, so the first cell is 0x7FFC
\pause
highlight li: 7 moves from the code into $t0
\pause
highlight addiu: the stack grows by one cell, $sp moves down
\pause
highlight sw: 7 moves from $t0 into the new cell
note: The value is copied. $t0 still holds 7.
