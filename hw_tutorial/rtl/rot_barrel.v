// rot_barrel.v -- fixed-size circular left rotator (chapter 04)
//
//   dout lane i = din lane (i + shift) mod N
//
// ceil(log2 N) stages. Stage k is N 2:1 muxes that rotate by 2^k when
// shift[k] is set. The shift value IS the control: no decoder needed.
// N may be any value (not only a power of two); a shift >= N simply
// rotates by shift mod N.
//
// Lane packing used by every module in this tutorial: lane i = bus[i*W +: W].
module rot_barrel #(
    parameter N  = 8,                         // number of lanes
    parameter W  = 8,                         // bits per lane (e.g. LLR width)
    parameter SW = (N > 1) ? $clog2(N) : 1    // shift width
) (
    input  wire [N*W-1:0] din,
    input  wire [SW-1:0]  shift,
    output wire [N*W-1:0] dout
);
    // stage[0] is the input, stage[SW] is the output
    wire [N*W-1:0] stage [0:SW];
    assign stage[0] = din;

    genvar k, i;
    generate
        for (k = 0; k < SW; k = k + 1) begin : g_stage
            for (i = 0; i < N; i = i + 1) begin : g_lane
                // source lane for "rotate by 2^k"; constant at elaboration time
                localparam SRC = (i + (1 << k)) % N;
                assign stage[k+1][i*W +: W] = shift[k] ? stage[k][SRC*W +: W]
                                                       : stage[k][i*W +: W];
            end
        end
    endgenerate

    assign dout = stage[SW];
endmodule
