module simple_cache(
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
  output        mem_req_valid,
  input         mem_req_ready,
  output        mem_req_write,
  output [7:0]  mem_req_addr,
  output [31:0] mem_req_wdata,
  input         mem_resp_valid,
  input  [31:0] mem_resp_rdata
);
  wire [3:0] addr_tag;
  wire [1:0] addr_index;
  wire [1:0] addr_offset;
  wire [3:0] line_tag;
  wire line_valid;
  wire [31:0] line_data;
  wire tag_write_enable;
  wire [1:0] tag_write_index;
  wire [3:0] tag_write_tag;
  wire data_write_enable;
  wire [1:0] data_write_index;
  wire [31:0] data_write_data;
  wire cache_hit;

  cache_address_decode decode(
    .addr(cpu_req_addr), .tag(addr_tag), .index(addr_index), .byte_offset(addr_offset)
  );
  cache_tag_array tags(
    .clk(clk), .reset(reset), .read_index(addr_index), .read_tag(line_tag), .read_valid(line_valid),
    .write_enable(tag_write_enable), .write_index(tag_write_index), .write_tag(tag_write_tag)
  );
  cache_data_array data(
    .clk(clk), .reset(reset), .read_index(addr_index), .read_data(line_data),
    .write_enable(data_write_enable), .write_index(data_write_index), .write_data(data_write_data)
  );
  cache_hit_logic hits(
    .req_tag(addr_tag), .line_tag(line_tag), .line_valid(line_valid), .hit(cache_hit)
  );
  cache_controller controller(
    .clk(clk), .reset(reset),
    .cpu_req_valid(cpu_req_valid), .cpu_req_ready(cpu_req_ready), .cpu_req_write(cpu_req_write),
    .cpu_req_addr(cpu_req_addr), .cpu_req_wdata(cpu_req_wdata),
    .cpu_resp_valid(cpu_resp_valid), .cpu_resp_rdata(cpu_resp_rdata), .cpu_resp_hit(cpu_resp_hit),
    .line_tag(line_tag), .line_valid(line_valid), .line_data(line_data), .cache_hit(cache_hit),
    .tag_write_enable(tag_write_enable), .tag_write_index(tag_write_index), .tag_write_tag(tag_write_tag),
    .data_write_enable(data_write_enable), .data_write_index(data_write_index), .data_write_data(data_write_data),
    .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write),
    .mem_req_addr(mem_req_addr), .mem_req_wdata(mem_req_wdata),
    .mem_resp_valid(mem_resp_valid), .mem_resp_rdata(mem_resp_rdata)
  );
endmodule
