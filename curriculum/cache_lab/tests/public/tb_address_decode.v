`timescale 1ns/1ps
module tb_address_decode;
  reg [7:0] addr;
  wire [3:0] tag;
  wire [1:0] index;
  wire [1:0] byte_offset;
  integer passed;
  integer failed;
  cache_address_decode dut(.addr(addr), .tag(tag), .index(index), .byte_offset(byte_offset));

  task check;
    input [7:0] a;
    input [3:0] expected_tag;
    input [1:0] expected_index;
    input [1:0] expected_offset;
    input [127:0] name;
    begin
      addr = a; #1;
      if (tag === expected_tag && index === expected_index && byte_offset === expected_offset) begin
        passed = passed + 1; $display("TUTOR_TEST %0s PASS", name);
      end else begin
        failed = failed + 1;
        $display("TUTOR_TEST %0s FAIL expected_tag=%h expected_index=%h expected_offset=%h actual_tag=%h actual_index=%h actual_offset=%h", name, expected_tag, expected_index, expected_offset, tag, index, byte_offset);
      end
      $display("TUTOR_TRACE addr=%h tag=%h index=%h byte_offset=%h", addr, tag, index, byte_offset);
    end
  endtask

  initial begin
    $dumpfile("wave.vcd"); $dumpvars(0, tb_address_decode);
    passed = 0; failed = 0;
    check(8'h00, 4'h0, 2'b00, 2'b00, "decode_00");
    check(8'h05, 4'h0, 2'b01, 2'b01, "decode_05");
    check(8'h14, 4'h1, 2'b01, 2'b00, "decode_14");
    check(8'hA7, 4'hA, 2'b01, 2'b11, "decode_A7");
    check(8'hFF, 4'hF, 2'b11, 2'b11, "decode_FF");
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed);
    $finish;
  end
endmodule
