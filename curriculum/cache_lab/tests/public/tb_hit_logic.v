`timescale 1ns/1ps
module tb_hit_logic;
  reg [3:0] req_tag, line_tag; reg line_valid; wire hit; integer passed; integer failed;
  cache_hit_logic dut(.req_tag(req_tag), .line_tag(line_tag), .line_valid(line_valid), .hit(hit));
  task check;
    input [3:0] r; input [3:0] l; input v; input expected; input [127:0] name;
    begin req_tag = r; line_tag = l; line_valid = v; #1; if (hit === expected) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL expected=%b actual=%b", name, expected, hit); end end
  endtask
  initial begin $dumpfile("wave.vcd"); $dumpvars(0, tb_hit_logic); passed = 0; failed = 0; check(1, 1, 1, 1, "valid_match"); check(1, 2, 1, 0, "valid_mismatch"); check(1, 1, 0, 0, "invalid_match"); check(0, 0, 0, 0, "invalid_zero"); $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish; end
endmodule
