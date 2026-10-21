`timescale 1ns/1ps
module tb_controller;
  reg clk, reset;
  reg cpu_req_valid, cpu_req_write;
  reg [7:0] cpu_req_addr; reg [31:0] cpu_req_wdata;
  wire cpu_req_ready, cpu_resp_valid, cpu_resp_hit;
  wire [31:0] cpu_resp_rdata;
  reg [3:0] tags [0:3]; reg valids [0:3]; reg [31:0] data [0:3];
  wire [3:0] line_tag = tags[cpu_req_addr[3:2]];
  wire line_valid = valids[cpu_req_addr[3:2]];
  wire [31:0] line_data = data[cpu_req_addr[3:2]];
  wire cache_hit = line_valid && (line_tag == cpu_req_addr[7:4]);
  wire tag_write_enable, data_write_enable;
  wire [1:0] tag_write_index, data_write_index;
  wire [3:0] tag_write_tag; wire [31:0] data_write_data;
  wire mem_req_valid, mem_req_ready, mem_req_write;
  wire [7:0] mem_req_addr; wire [31:0] mem_req_wdata;
  reg mem_resp_valid; reg [31:0] mem_resp_rdata;
  reg [31:0] memory [0:63]; reg pending; reg pending_write; reg [7:0] pending_addr; reg [31:0] pending_data;
  integer i; integer passed; integer failed;

  cache_controller dut(
    .clk(clk), .reset(reset), .cpu_req_valid(cpu_req_valid), .cpu_req_ready(cpu_req_ready), .cpu_req_write(cpu_req_write), .cpu_req_addr(cpu_req_addr), .cpu_req_wdata(cpu_req_wdata),
    .cpu_resp_valid(cpu_resp_valid), .cpu_resp_rdata(cpu_resp_rdata), .cpu_resp_hit(cpu_resp_hit), .line_tag(line_tag), .line_valid(line_valid), .line_data(line_data), .cache_hit(cache_hit),
    .tag_write_enable(tag_write_enable), .tag_write_index(tag_write_index), .tag_write_tag(tag_write_tag), .data_write_enable(data_write_enable), .data_write_index(data_write_index), .data_write_data(data_write_data),
    .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write), .mem_req_addr(mem_req_addr), .mem_req_wdata(mem_req_wdata), .mem_resp_valid(mem_resp_valid), .mem_resp_rdata(mem_resp_rdata)
  );
  assign mem_req_ready = 1'b1;
  always #5 clk = ~clk;

  always @(posedge clk) begin
    mem_resp_valid <= pending;
    if (pending) begin
      if (pending_write) begin memory[pending_addr[7:2]] <= pending_data; mem_resp_rdata <= 0; end
      else mem_resp_rdata <= memory[pending_addr[7:2]];
    end
    pending <= 1'b0;
    if (mem_req_valid && mem_req_ready) begin pending <= 1'b1; pending_write <= mem_req_write; pending_addr <= mem_req_addr; pending_data <= mem_req_wdata; end
    if (tag_write_enable) begin tags[tag_write_index] <= tag_write_tag; valids[tag_write_index] <= 1'b1; end
    if (data_write_enable) data[data_write_index] <= data_write_data;
  end

  task check_response;
    input [31:0] expected_data; input expected_hit; input [127:0] name;
    begin
      wait (cpu_resp_valid === 1'b1); #1;
      if (cpu_resp_rdata === expected_data && cpu_resp_hit === expected_hit) begin passed = passed + 1; $display("TUTOR_TEST %0s PASS", name); end
      else begin failed = failed + 1; $display("TUTOR_TEST %0s FAIL expected_data=%h expected_hit=%b actual_data=%h actual_hit=%b", name, expected_data, expected_hit, cpu_resp_rdata, cpu_resp_hit); end
    end
  endtask

  task request;
    input write; input [7:0] addr; input [31:0] wdata; input [31:0] expected_data; input expected_hit; input [127:0] name;
    begin
      @(negedge clk); cpu_req_write = write; cpu_req_addr = addr; cpu_req_wdata = wdata; cpu_req_valid = 1'b1;
      while (!cpu_req_ready) @(negedge clk);
      @(posedge clk); #1; cpu_req_valid = 1'b0;
      check_response(expected_data, expected_hit, name);
      @(posedge clk);
    end
  endtask

  initial begin
    $dumpfile("wave.vcd"); $dumpvars(0, tb_controller);
    clk = 0; reset = 1; cpu_req_valid = 0; cpu_req_write = 0; cpu_req_addr = 0; cpu_req_wdata = 0; mem_resp_valid = 0; mem_resp_rdata = 0; pending = 0; passed = 0; failed = 0;
    for (i = 0; i < 4; i = i + 1) begin tags[i] = 0; valids[i] = 0; data[i] = 0; end
    for (i = 0; i < 64; i = i + 1) memory[i] = 32'h20000000 + i;
    repeat (2) @(posedge clk); #1; reset = 0;
    request(0, 8'h24, memory[8'h24 >> 2], 32'h20000009, 0, "read_miss");
    request(0, 8'h24, 0, 32'h20000009, 1, "read_hit");
    request(1, 8'h24, 32'hCAFEBABE, 0, 1, "write_hit");
    if (memory[8'h24 >> 2] === 32'hCAFEBABE) begin passed = passed + 1; $display("TUTOR_TEST write_through PASS"); end else begin failed = failed + 1; $display("TUTOR_TEST write_through FAIL"); end
    $display("TUTOR_SUMMARY passed=%0d failed=%0d", passed, failed); $finish;
  end
endmodule
