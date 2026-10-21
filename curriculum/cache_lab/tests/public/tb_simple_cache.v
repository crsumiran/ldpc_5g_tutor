`timescale 1ns/1ps
module tb_simple_cache;
  reg clk, reset, cpu_req_valid, cpu_req_write; reg [7:0] cpu_req_addr; reg [31:0] cpu_req_wdata;
  wire cpu_req_ready, cpu_resp_valid, cpu_resp_hit; wire [31:0] cpu_resp_rdata;
  wire mem_req_valid, mem_req_ready, mem_req_write; wire [7:0] mem_req_addr; wire [31:0] mem_req_wdata; wire mem_resp_valid; wire [31:0] mem_resp_rdata;
  integer passed; integer failed;
  simple_cache dut(.clk(clk), .reset(reset), .cpu_req_valid(cpu_req_valid), .cpu_req_ready(cpu_req_ready), .cpu_req_write(cpu_req_write), .cpu_req_addr(cpu_req_addr), .cpu_req_wdata(cpu_req_wdata), .cpu_resp_valid(cpu_resp_valid), .cpu_resp_rdata(cpu_resp_rdata), .cpu_resp_hit(cpu_resp_hit), .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write), .mem_req_addr(mem_req_addr), .mem_req_wdata(mem_req_wdata), .mem_resp_valid(mem_resp_valid), .mem_resp_rdata(mem_resp_rdata));
  backing_memory mem(.clk(clk), .reset(reset), .req_valid(mem_req_valid), .req_ready(mem_req_ready), .req_write(mem_req_write), .req_addr(mem_req_addr), .req_wdata(mem_req_wdata), .resp_valid(mem_resp_valid), .resp_rdata(mem_resp_rdata));
  always #5 clk = ~clk;
  task request;
    input write; input [7:0] addr; input [31:0] wdata; input [31:0] expected; input expected_hit; input [127:0] name;
    begin @(negedge clk); cpu_req_write = write; cpu_req_addr = addr; cpu_req_wdata = wdata; cpu_req_valid = 1; while (!cpu_req_ready) @(negedge clk); @(posedge clk); #1; cpu_req_valid = 0; while (!cpu_resp_valid) @(posedge clk); #1; if (cpu_resp_rdata === expected && cpu_resp_hit === expected_hit) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL expected_data=%h expected_hit=%b actual_data=%h actual_hit=%b", name, expected, expected_hit, cpu_resp_rdata, cpu_resp_hit); end @(posedge clk); end
  endtask
  initial begin
    $dumpfile("wave.vcd"); $dumpvars(0, tb_simple_cache);
    clk = 0; reset = 1; cpu_req_valid = 0; cpu_req_write = 0; cpu_req_addr = 0; cpu_req_wdata = 0; passed = 0; failed = 0;
    repeat (2) @(posedge clk); #1; reset = 0; mem.set_word(8'h00, 32'h11111111); mem.set_word(8'h10, 32'h22222222); mem.set_word(8'h20, 32'h33333333);
    request(0, 8'h00, 0, 32'h11111111, 0, "cold_miss");
    request(0, 8'h00, 0, 32'h11111111, 1, "warm_hit");
    request(0, 8'h10, 0, 32'h22222222, 0, "conflict_miss");
    request(1, 8'h10, 32'hABCDEF01, 0, 1, "write_hit");
    request(0, 8'h10, 0, 32'hABCDEF01, 1, "updated_hit");
    request(1, 8'h20, 32'hDEADBEEF, 0, 0, "write_miss_no_allocate");
    request(0, 8'h20, 0, 32'hDEADBEEF, 0, "read_after_write_miss");
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish;
  end
endmodule
