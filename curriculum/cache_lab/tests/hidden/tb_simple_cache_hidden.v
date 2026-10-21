`timescale 1ns/1ps
module slow_memory(
  input clk, input reset, input req_valid, output req_ready, input req_write, input [7:0] req_addr, input [31:0] req_wdata,
  output reg resp_valid, output reg [31:0] resp_rdata
);
  reg [31:0] words [0:63]; reg [2:0] delay; reg pending; reg pending_write; reg [7:0] pending_addr; reg [31:0] pending_data; integer i;
  assign req_ready = (delay == 0) && !pending;
  always @(posedge clk) begin
    resp_valid <= 0;
    if (reset) begin delay <= 2; pending <= 0; for (i = 0; i < 64; i = i + 1) words[i] <= 32'h40000000 + i; end
    else begin
      if (delay != 0) delay <= delay - 1;
      if (pending) begin if (pending_write) begin words[pending_addr[7:2]] <= pending_data; resp_rdata <= 0; end else resp_rdata <= words[pending_addr[7:2]]; resp_valid <= 1; pending <= 0; delay <= 2; end
      if (req_valid && req_ready) begin pending <= 1; pending_write <= req_write; pending_addr <= req_addr; pending_data <= req_wdata; end
    end
  end
  task set_word; input [7:0] addr; input [31:0] data; begin words[addr[7:2]] = data; end endtask
endmodule

module tb_simple_cache_hidden;
  reg clk, reset, cpu_req_valid, cpu_req_write; reg [7:0] cpu_req_addr; reg [31:0] cpu_req_wdata;
  wire cpu_req_ready, cpu_resp_valid, cpu_resp_hit; wire [31:0] cpu_resp_rdata; wire mem_req_valid, mem_req_ready, mem_req_write; wire [7:0] mem_req_addr; wire [31:0] mem_req_wdata; wire mem_resp_valid; wire [31:0] mem_resp_rdata;
  integer passed; integer failed;
  simple_cache dut(.clk(clk), .reset(reset), .cpu_req_valid(cpu_req_valid), .cpu_req_ready(cpu_req_ready), .cpu_req_write(cpu_req_write), .cpu_req_addr(cpu_req_addr), .cpu_req_wdata(cpu_req_wdata), .cpu_resp_valid(cpu_resp_valid), .cpu_resp_rdata(cpu_resp_rdata), .cpu_resp_hit(cpu_resp_hit), .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write), .mem_req_addr(mem_req_addr), .mem_req_wdata(mem_req_wdata), .mem_resp_valid(mem_resp_valid), .mem_resp_rdata(mem_resp_rdata));
  slow_memory mem(.clk(clk), .reset(reset), .req_valid(mem_req_valid), .req_ready(mem_req_ready), .req_write(mem_req_write), .req_addr(mem_req_addr), .req_wdata(mem_req_wdata), .resp_valid(mem_resp_valid), .resp_rdata(mem_resp_rdata));
  always #1 clk = ~clk;
  task request;
    input write; input [7:0] addr; input [31:0] wdata; input [31:0] expected; input expected_hit; input [127:0] name;
    begin @(negedge clk); cpu_req_write = write; cpu_req_addr = addr; cpu_req_wdata = wdata; cpu_req_valid = 1; while (!cpu_req_ready) @(negedge clk); @(posedge clk); #0.2; cpu_req_valid = 0; while (!cpu_resp_valid) @(posedge clk); #0.2; if (cpu_resp_rdata === expected && cpu_resp_hit === expected_hit) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL", name); end @(posedge clk); end
  endtask
  initial begin clk = 0; reset = 1; cpu_req_valid = 0; cpu_req_write = 0; cpu_req_addr = 0; cpu_req_wdata = 0; passed = 0; failed = 0; repeat (4) @(posedge clk); #0.2; reset = 0; mem.set_word(8'h00, 32'h55555555); mem.set_word(8'h10, 32'h66666666); request(0, 8'h00, 0, 32'h55555555, 0, "stall_cold_miss"); request(0, 8'h00, 0, 32'h55555555, 1, "stall_warm_hit"); request(0, 8'h10, 0, 32'h66666666, 0, "stall_conflict"); $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish; end
endmodule
