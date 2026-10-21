`timescale 1ns/1ps
module tb_and2;
  reg a, b;
  wire y;
  and2 dut(.a(a), .b(b), .y(y));
  integer errors;
  initial begin
    errors = 0;
    a = 0; b = 0; #1; if (y !== 1'b0) errors = errors + 1;
    a = 0; b = 1; #1; if (y !== 1'b0) errors = errors + 1;
    a = 1; b = 0; #1; if (y !== 1'b0) errors = errors + 1;
    a = 1; b = 1; #1; if (y !== 1'b1) errors = errors + 1;
    if (errors == 0) $display("ALL_TESTS_PASSED");
    else $display("TESTS_FAILED %0d", errors);
    $finish;
  end
endmodule