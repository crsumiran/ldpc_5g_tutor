module backing_memory(
  input         clk,
  input         reset,
  input         req_valid,
  output        req_ready,
  input         req_write,
  input  [7:0]  req_addr,
  input  [31:0] req_wdata,
  output reg    resp_valid,
  output reg [31:0] resp_rdata
);
  reg [31:0] words [0:63];
  integer i;

  assign req_ready = 1'b1;

  always @(posedge clk) begin
    resp_valid <= 1'b0;
    if (reset) begin
      for (i = 0; i < 64; i = i + 1)
        words[i] <= 32'h10000000 + i;
    end else if (req_valid && req_ready) begin
      if (req_write) begin
        words[req_addr[7:2]] <= req_wdata;
        resp_rdata <= 32'b0;
      end else begin
        resp_rdata <= words[req_addr[7:2]];
      end
      resp_valid <= 1'b1;
    end
  end

  task set_word;
    input [7:0] addr;
    input [31:0] data;
    begin words[addr[7:2]] = data; end
  endtask

  function [31:0] get_word;
    input [7:0] addr;
    begin get_word = words[addr[7:2]]; end
  endfunction
endmodule
