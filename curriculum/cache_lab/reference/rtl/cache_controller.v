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
  localparam S_IDLE = 3'd0;
  localparam S_READ_REQ = 3'd1;
  localparam S_READ_WAIT = 3'd2;
  localparam S_WRITE_REQ = 3'd3;
  localparam S_WRITE_WAIT = 3'd4;
  localparam S_RESP = 3'd5;

  reg [2:0] state;
  reg saved_write;
  reg [7:0] saved_addr;
  reg [31:0] saved_wdata;
  reg [31:0] response_data;
  reg response_hit;

  wire [3:0] request_tag = cpu_req_addr[7:4];
  wire [1:0] request_index = cpu_req_addr[3:2];
  assign cpu_req_ready = (state == S_IDLE) && !reset;
  assign cpu_resp_valid = (state == S_RESP);
  assign cpu_resp_rdata = response_data;
  assign cpu_resp_hit = response_hit;

  assign tag_write_enable = (state == S_READ_WAIT) && mem_resp_valid;
  assign tag_write_index = saved_addr[3:2];
  assign tag_write_tag = saved_addr[7:4];
  assign data_write_enable = ((state == S_READ_WAIT) && mem_resp_valid) ||
                             ((state == S_IDLE) && cpu_req_valid && cpu_req_ready && cpu_req_write && cache_hit);
  assign data_write_index = (state == S_READ_WAIT) ? saved_addr[3:2] : cpu_req_addr[3:2];
  assign data_write_data = (state == S_READ_WAIT) ? mem_resp_rdata : cpu_req_wdata;

  assign mem_req_valid = (state == S_READ_REQ) || (state == S_WRITE_REQ);
  assign mem_req_write = (state == S_WRITE_REQ);
  assign mem_req_addr = saved_addr;
  assign mem_req_wdata = saved_wdata;

  always @(posedge clk) begin
    if (reset) begin
      state <= S_IDLE;
      saved_write <= 1'b0;
      saved_addr <= 8'b0;
      saved_wdata <= 32'b0;
      response_data <= 32'b0;
      response_hit <= 1'b0;
    end else begin
      case (state)
        S_IDLE: begin
          if (cpu_req_valid && cpu_req_ready) begin
            saved_write <= cpu_req_write;
            saved_addr <= cpu_req_addr;
            saved_wdata <= cpu_req_wdata;
            if (cache_hit) begin
              response_hit <= 1'b1;
              response_data <= cpu_req_write ? 32'b0 : line_data;
              if (cpu_req_write)
                state <= S_WRITE_REQ;
              else
                state <= S_RESP;
            end else begin
              response_hit <= 1'b0;
              response_data <= 32'b0;
              if (cpu_req_write)
                state <= S_WRITE_REQ;
              else
                state <= S_READ_REQ;
            end
          end
        end
        S_READ_REQ: begin
          if (mem_req_valid && mem_req_ready)
            state <= S_READ_WAIT;
        end
        S_READ_WAIT: begin
          if (mem_resp_valid) begin
            response_data <= mem_resp_rdata;
            state <= S_RESP;
          end
        end
        S_WRITE_REQ: begin
          if (mem_req_valid && mem_req_ready)
            state <= S_WRITE_WAIT;
        end
        S_WRITE_WAIT: begin
          if (mem_resp_valid)
            state <= S_RESP;
        end
        S_RESP: begin
          state <= S_IDLE;
        end
        default: state <= S_IDLE;
      endcase
    end
  end
endmodule
