// rot_qsn.v -- variable-size circular left rotator, QSN style (chapter 05)
//
//   for i < z :  dout lane i = din lane (i + shift) mod z
//   for i >= z:  dout lane i = 0 (unused lanes)
//
// Requires 0 <= shift < z <= N. A plain N-lane barrel rotator cannot do
// this when z < N: its wrap-around point is fixed at lane N, not lane z.
// Fix: two NON-circular shifters plus a per-lane merge.
//
//   left  = din << shift          (lane i gets din[i+shift])  valid for i <  z-shift
//   right = din >> (z - shift)    (lane i gets din[i-z+shift]) valid for i >= z-shift
//   dout  = (i < z-shift) ? left : right
//
// Reference: Chen, Lin, Akella, "QSN -- a simple circular-shift network for
// reconfigurable quasi-cyclic LDPC decoders", IEEE TCAS-II 57(10), 2010.
module rot_qsn #(
    parameter N  = 384,
    parameter W  = 8,
    parameter SW = $clog2(N),       // shift width
    parameter ZW = $clog2(N + 1)    // z width (must hold N itself)
) (
    input  wire [N*W-1:0] din,
    input  wire [ZW-1:0]  z,
    input  wire [SW-1:0]  shift,
    output wire [N*W-1:0] dout
);
    wire [ZW-1:0] lshift = shift;         // amount for the left shifter (zero-extended)
    wire [ZW-1:0] rshift = z - shift;     // amount for the right shifter

    // Two logarithmic (non-circular) shifters, zero fill.
    wire [N*W-1:0] ls [0:ZW];
    wire [N*W-1:0] rs [0:ZW];
    assign ls[0] = din;
    assign rs[0] = din;

    genvar k, i;
    generate
        for (k = 0; k < ZW; k = k + 1) begin : g_stage
            for (i = 0; i < N; i = i + 1) begin : g_lane
                localparam D = (1 << k);
                if (i + D < N) begin : g_l
                    assign ls[k+1][i*W +: W] = lshift[k] ? ls[k][(i+D)*W +: W] : ls[k][i*W +: W];
                end else begin : g_lz
                    assign ls[k+1][i*W +: W] = lshift[k] ? {W{1'b0}} : ls[k][i*W +: W];
                end
                if (i >= D) begin : g_r
                    assign rs[k+1][i*W +: W] = rshift[k] ? rs[k][(i-D)*W +: W] : rs[k][i*W +: W];
                end else begin : g_rz
                    assign rs[k+1][i*W +: W] = rshift[k] ? {W{1'b0}} : rs[k][i*W +: W];
                end
            end
        end

        // Merge network: one 2:1 mux per lane, select is a thermometer code of (z - shift)
        for (i = 0; i < N; i = i + 1) begin : g_merge
            wire use_left = (i < rshift);
            wire valid    = (i < z);
            assign dout[i*W +: W] = !valid   ? {W{1'b0}} :
                                    use_left ? ls[ZW][i*W +: W] : rs[ZW][i*W +: W];
        end
    endgenerate
endmodule
