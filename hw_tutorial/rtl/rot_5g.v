// rot_5g.v -- 5G NR rotator: any lifting size Z <= 384, any shift (chapter 06)
//
//   for i < z :  dout lane i = din lane (i + shift) mod z
//   for i >= z:  dout lane i = 0
//
// Bypass ("two rotators + merge") structure built from two full-size cyclic
// rotators, here IBNs, so any of the 51 NR lifting sizes works:
//
//   A = rotl_N(din, shift)                 correct for lanes i <  z-shift
//   B = rotl_N(din, (N - z + shift) mod N) correct for lanes i >= z-shift
//   dout lane i = (i < z-shift) ? A : B
//
// Requires 0 <= shift < z <= N.
module rot_5g #(
    parameter M  = 128,             // N = 3*M = 384 for 5G NR
    parameter W  = 8,
    parameter N  = 3 * M,
    parameter SW = $clog2(N),
    parameter ZW = $clog2(N + 1)
) (
    input  wire [N*W-1:0] din,
    input  wire [ZW-1:0]  z,
    input  wire [SW-1:0]  shift,
    output wire [N*W-1:0] dout
);
    wire [ZW-1:0] split = z - shift;                // first lane taken from B

    // second shift = (N - z + shift) mod N; N - z + shift is in [1, N], so
    // at most one conditional subtract.
    localparam [ZW:0] NN = N;
    wire [ZW:0]   s2_raw = NN - {1'b0, z} + {{(ZW+1-SW){1'b0}}, shift};
    wire [ZW:0]   s2_mod = (s2_raw >= NN) ? s2_raw - NN : s2_raw;
    wire [SW-1:0] s2     = s2_mod[SW-1:0];

    wire [N*W-1:0] rot_a, rot_b;
    rot_ibn3 #(.M(M), .W(W)) u_a (.din(din), .shift(shift), .dout(rot_a));
    rot_ibn3 #(.M(M), .W(W)) u_b (.din(din), .shift(s2),    .dout(rot_b));

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_merge
            assign dout[i*W +: W] = (i >= z)    ? {W{1'b0}} :
                                    (i < split) ? rot_a[i*W +: W] : rot_b[i*W +: W];
        end
    endgenerate
endmodule
