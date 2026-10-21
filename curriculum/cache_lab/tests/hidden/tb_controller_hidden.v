`timescale 1ns/1ps
module delayed_memory(
  input clk, input reset, input req_valid, output req_ready, input req_write, input [7:0] req_addr, input [31:0] req_wdata,
  output reg resp_valid, output reg [31:0] resp_rdata
);
  reg [31:0] words [0:63]; reg [2:0] wait_count; reg pending; reg pending_write; reg [7:0] pending_addr; reg [31:0] pending_data; integer i;
  assign req_ready = (wait_count == 0) && !pending;
  always @(posedge clk) begin
    resp_valid <= 0;
    if (reset) begin wait_count <= 3; pending <= 0; for (i = 0; i < 64; i = i + 1) words[i] <= 32'h30000000 + i; end
    else begin
      if (wait_count != 0) wait_count <= wait_count - 1;
      if (pending) begin
        if (pending_write) begin words[pending_addr[7:2]] <= pending_data; resp_rdata <= 0; end else resp_rdata <= words[pending_addr[7:2]];
        resp_valid <= 1; pending <= 0; wait_count <= 2;
      end
      if (req_valid && req_ready) begin pending <= 1; pending_write <= req_write; pending_addr <= req_addr; pending_data <= req_wdata; end
    end
  end
endmodule

module tb_controller_hidden;
  reg clk, reset, cpu_req_valid, cpu_req_write; reg [7:0] cpu_req_addr; reg [31:0] cpu_req_wdata;
  wire cpu_req_ready, cpu_resp_valid, cpu_resp_hit; wire [31:0] cpu_resp_rdata;
  reg [3:0] tags [0:3]; reg valids [0:3]; reg [31:0] data [0:3];
  wire [3:0] line_tag = tags[cpu_req_addr[3:2]]; wire line_valid = valids[cpu_req_addr[3:2]]; wire [31:0] line_data = data[cpu_req_addr[3:2]]; wire cache_hit = line_valid && (line_tag == cpu_req_addr[7:4]);
  wire tag_write_enable, data_write_enable; wire [1:0] tag_write_index, data_write_index; wire [3:0] tag_write_tag; wire [31:0] data_write_data;
  wire mem_req_valid, mem_req_ready, mem_req_write; wire [7:0] mem_req_addr; wire [31:0] mem_req_wdata; wire mem_resp_valid; wire [31:0] mem_resp_rdata;
  integer i; integer passed; integer failed;
  delayed_memory mem(.clk(clk), .reset(reset), .req_valid(mem_req_valid), .req_ready(mem_req_ready), .req_write(mem_req_write), .req_addr(mem_req_addr), .req_wdata(mem_req_wdata), .resp_valid(mem_resp_valid), .resp_rdata(mem_resp_rdata));
  cache_controller dut(.clk(clk), .reset(reset), .cpu_req_valid(cpu_req_valid), .cpu_req_ready(cpu_req_ready), .cpu_req_write(cpu_req_write), .cpu_req_addr(cpu_req_addr), .cpu_req_wdata(cpu_req_wdata), .cpu_resp_valid(cpu_resp_valid), .cpu_resp_rdata(cpu_resp_rdata), .cpu_resp_hit(cpu_resp_hit), .line_tag(line_tag), .line_valid(line_valid), .line_data(line_data), .cache_hit(cache_hit), .tag_write_enable(tag_write_enable), .tag_write_index(tag_write_index), .tag_write_tag(tag_write_tag), .data_write_enable(data_write_enable), .data_write_index(data_write_index), .data_write_data(data_write_data), .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write), .mem_req_addr(mem_req_addr), .mem_req_wdata(mem_req_wdata), .mem_resp_valid(mem_resp_valid), .mem_resp_rdata(mem_resp_rdata));
  always #1 clk = ~clk;
  always @(posedge clk) begin if (tag_write_enable) begin tags[tag_write_index] <= tag_write_tag; valids[tag_write_index] <= 1; end if (data_write_enable) data[data_write_index] <= data_write_data; end
  task request;
    input [7:0] addr; input [31:0] expected; input expected_hit; input [127:0] name;
    begin @(negedge clk); cpu_req_addr = addr; cpu_req_write = 0; cpu_req_wdata = 0; cpu_req_valid = 1; while (!cpu_req_ready) @(negedge clk); @(posedge clk); #0.2; cpu_req_valid = 0; wait (cpu_resp_valid === 1'b1); #0.2; if (cpu_resp_rdata === expected && cpu_resp_hit === expected_hit) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL", name); end @(posedge clk); end
  endtask
  initial begin clk = 0; reset = 1; cpu_req_valid = 0; cpu_req_write = 0; cpu_req_addr = 0; cpu_req_wdata = 0; passed = 0; failed = 0; for (i = 0; i < 4; i = i + 1) begin tags[i] = 0; valids[i] = 0; data[i] = 0; end repeat (4) @(posedge clk); #0.2; reset = 0; request(8'h10, 32'h30000004, 0, "stalled_read_miss"); request(8'h10, 32'h30000004, 1, "second_read_hit"); $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish; end
endmodule
