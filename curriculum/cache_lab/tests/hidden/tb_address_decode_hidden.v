`timescale 1ns/1ps
module tb_address_decode_hidden;
  reg [7:0] addr;
  wire [3:0] tag;
  wire [1:0] index;
  wire [1:0] byte_offset;
  integer a;
  integer passed;
  integer failed;
  cache_address_decode dut(.addr(addr), .tag(tag), .index(index), .byte_offset(byte_offset));
  initial begin
    passed = 0; failed = 0;
    for (a = 0; a < 256; a = a + 1) begin
      addr = a[7:0]; #1;
      if (tag === addr[7:4] && index === addr[3:2] && byte_offset === addr[1:0]) passed = passed + 1;
      else failed = failed + 1;
    end
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed);
    $finish;
  end
endmodule
