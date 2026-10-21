`timescale 1ns/1ps
module tb_data_array;
  reg clk, reset, write_enable; reg [1:0] read_index, write_index; reg [31:0] write_data;
  wire [31:0] read_data; integer passed; integer failed;
  cache_data_array dut(.clk(clk), .reset(reset), .read_index(read_index), .read_data(read_data), .write_enable(write_enable), .write_index(write_index), .write_data(write_data));
  always #5 clk = ~clk;
  task check;
    input [1:0] idx; input [31:0] expected; input [127:0] name;
    begin read_index = idx; #1; if (read_data === expected) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL expected=%h actual=%h", name, expected, read_data); end end
  endtask
  initial begin
    $dumpfile("wave.vcd"); $dumpvars(0, tb_data_array);
    clk = 0; reset = 1; write_enable = 0; read_index = 0; write_index = 0; write_data = 0; passed = 0; failed = 0;
    @(posedge clk); #1; reset = 0; check(0, 0, "reset_zero");
    write_index = 1; write_data = 32'hDEADBEEF; write_enable = 1; @(posedge clk); #1; write_enable = 0;
    check(1, 32'hDEADBEEF, "write_line_1"); check(0, 0, "preserve_line_0");
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish;
  end
endmodule
