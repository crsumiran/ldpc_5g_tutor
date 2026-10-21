`timescale 1ns/1ps
module tb_data_array_hidden;
  reg clk, reset, write_enable; reg [1:0] read_index, write_index; reg [31:0] write_data;
  wire [31:0] read_data; integer i; integer passed; integer failed;
  cache_data_array dut(.clk(clk), .reset(reset), .read_index(read_index), .read_data(read_data), .write_enable(write_enable), .write_index(write_index), .write_data(write_data));
  always #1 clk = ~clk;
  initial begin
    clk = 0; reset = 1; write_enable = 0; read_index = 0; write_index = 0; write_data = 0; passed = 0; failed = 0;
    @(posedge clk); #0.2; reset = 0;
    for (i = 0; i < 4; i = i + 1) begin write_index = i[1:0]; write_data = 32'hA0000000 + i; write_enable = 1; @(posedge clk); #0.2; write_enable = 0; end
    for (i = 0; i < 4; i = i + 1) begin read_index = i[1:0]; #0.2; if (read_data === (32'hA0000000 + i)) passed = passed + 1; else failed = failed + 1; end
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish;
  end
endmodule
