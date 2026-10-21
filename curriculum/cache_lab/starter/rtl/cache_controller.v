module cache_controller(
  input         clk,
  input         reset,
  input         cpu_req_valid,
  output        cpu_req_ready,
  input         cpu_req_write,
  input  [7:0]  cpu_req_addr,
  input  [31:0] cpu_req_wdata,
  output        cpu_resp_valid,
  output [31:0] cpu_resp_rdata,
  output        cpu_resp_hit,
  input  [3:0]  line_tag,
  input         line_valid,
  input  [31:0] line_data,
  input         cache_hit,
  output        tag_write_enable,
  output [1:0]  tag_write_index,
  output [3:0]  tag_write_tag,
  output        data_write_enable,
  output [1:0]  data_write_index,
  output [31:0] data_write_data,
  output        mem_req_valid,
  input         mem_req_ready,
  output        mem_req_write,
  output [7:0]  mem_req_addr,
  output [31:0] mem_req_wdata,
  input         mem_resp_valid,
  input  [31:0] mem_resp_rdata
);
  // TODO: implement the blocking cache FSM.
  assign cpu_req_ready = 1'b0;
  assign cpu_resp_valid = 1'b0;
  assign cpu_resp_rdata = 32'b0;
  assign cpu_resp_hit = 1'b0;
  assign tag_write_enable = 1'b0;
  assign tag_write_index = 2'b0;
  assign tag_write_tag = 4'b0;
  assign data_write_enable = 1'b0;
  assign data_write_index = 2'b0;
  assign data_write_data = 32'b0;
  assign mem_req_valid = 1'b0;
  assign mem_req_write = 1'b0;
  assign mem_req_addr = 8'b0;
  assign mem_req_wdata = 32'b0;
endmodule
