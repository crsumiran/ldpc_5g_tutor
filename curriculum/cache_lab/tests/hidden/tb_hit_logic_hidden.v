`timescale 1ns/1ps
module tb_hit_logic_hidden;
  reg [3:0] req_tag, line_tag; reg line_valid; wire hit; integer r; integer l; integer v; integer passed; integer failed;
  cache_hit_logic dut(.req_tag(req_tag), .line_tag(line_tag), .line_valid(line_valid), .hit(hit));
  initial begin passed = 0; failed = 0; for (v = 0; v < 2; v = v + 1) for (r = 0; r < 16; r = r + 1) for (l = 0; l < 16; l = l + 1) begin req_tag = r; line_tag = l; line_valid = v; #0.1; if (hit === (v && (r == l))) passed = passed + 1; else failed = failed + 1; end $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish; end
endmodule
