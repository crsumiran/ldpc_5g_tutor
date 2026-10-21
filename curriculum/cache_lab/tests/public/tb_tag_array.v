`timescale 1ns/1ps
module tb_tag_array;
  reg clk, reset, write_enable;
  reg [1:0] read_index, write_index;
  reg [3:0] write_tag;
  wire [3:0] read_tag;
  wire read_valid;
  integer passed; integer failed;
  cache_tag_array dut(.clk(clk), .reset(reset), .read_index(read_index), .read_tag(read_tag), .read_valid(read_valid), .write_enable(write_enable), .write_index(write_index), .write_tag(write_tag));
  always #5 clk = ~clk;

  task check;
    input [1:0] idx; input [3:0] expected_tag; input expected_valid; input [127:0] name;
    begin
      read_index = idx; #1;
      if (read_tag === expected_tag && read_valid === expected_valid) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end
      else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL expected_tag=%h expected_valid=%b actual_tag=%h actual_valid=%b", name, expected_tag, expected_valid, read_tag, read_valid); end
    end
  endtask

  initial begin
    $dumpfile("wave.vcd"); $dumpvars(0, tb_tag_array);
    clk = 0; reset = 1; write_enable = 0; read_index = 0; write_index = 0; write_tag = 0; passed = 0; failed = 0;
    @(posedge clk); #1; reset = 0;
    check(0, 0, 0, "reset_line_0"); check(3, 0, 0, "reset_line_3");
    write_index = 2; write_tag = 4'hB; write_enable = 1; @(posedge clk); #1; write_enable = 0;
    check(2, 4'hB, 1, "write_line_2"); check(1, 0, 0, "preserve_line_1");
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish;
  end
endmodule
