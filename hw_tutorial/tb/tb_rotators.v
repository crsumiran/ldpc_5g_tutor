// tb_rotators.v -- self-checking testbench for every rotator in ../rtl
//
// Fixed-size rotators: every shift, random lane data.
// Variable-size rotators: every one of the 51 NR lifting sizes x every shift.
// Reference: expected lane i = din lane (i + shift) mod z, lanes >= z must be 0.
`timescale 1ns/1ps
module tb_rotators;
    localparam W  = 8;
    localparam N  = 384;
    localparam SW = 9;
    localparam ZW = 9;

    // ---------------- stimulus
    reg  [N*W-1:0] din;
    reg  [SW-1:0]  shift;
    reg  [ZW-1:0]  z;

    // ---------------- DUTs
    wire [7*W-1:0]   d_b7;       // paper Fig. 2: 7-lane barrel
    wire [N*W-1:0]   d_b384;
    wire [128*W-1:0] d_ban;
    wire [N*W-1:0]   d_ibn;
    wire [N*W-1:0]   d_qsn;
    wire [N*W-1:0]   d_5g;

    rot_barrel #(.N(7),   .W(W)) u_b7   (.din(din[7*W-1:0]),   .shift(shift[2:0]), .dout(d_b7));
    rot_barrel #(.N(N),   .W(W)) u_b384 (.din(din),            .shift(shift),      .dout(d_b384));
    rot_banyan #(.N(128), .W(W)) u_ban  (.din(din[128*W-1:0]), .shift(shift[6:0]), .dout(d_ban));
    rot_ibn3   #(.M(128), .W(W)) u_ibn  (.din(din),            .shift(shift),      .dout(d_ibn));
    rot_qsn    #(.N(N),   .W(W)) u_qsn  (.din(din), .z(z),     .shift(shift),      .dout(d_qsn));
    rot_5g     #(.M(128), .W(W)) u_5g   (.din(din), .z(z),     .shift(shift),      .dout(d_5g));

    // ---------------- checking
    integer errors = 0, checks = 0;

    // Build the word in a temporary and assign din ONCE: Verilator does not
    // re-evaluate downstream logic for part-select writes made inside a task.
    task randomize_din;
        integer i;
        reg [N*W-1:0] t;
        begin
            for (i = 0; i < N; i = i + 1) t[i*W +: W] = $random;
            din = t;
        end
    endtask

    // compare the first `nl` lanes of `got` against rotl(din, shift) mod zz;
    // lanes in [zz, nl) must be zero when check_zero is set
    task check;
        input [8*16-1:0] name;
        input [N*W-1:0]  got;
        input integer    nl, zz, check_zero;
        integer i;
        reg [W-1:0] exp;
        begin
            checks = checks + 1;
            for (i = 0; i < nl; i = i + 1) begin
                exp = (i < zz) ? din[((i + shift) % zz)*W +: W] : {W{1'b0}};
                if ((i < zz || check_zero) && got[i*W +: W] !== exp) begin
                    if (errors < 10)
                        $display("FAIL %0s z=%0d shift=%0d lane=%0d got=%h exp=%h",
                                 name, zz, shift, i, got[i*W +: W], exp);
                    errors = errors + 1;
                end
            end
        end
    endtask

    // 5G NR lifting sizes, TS 38.212 Table 5.3.2-1
    integer nr_z [0:50];
    integer zi, s;
    initial begin
        nr_z[ 0]=2;   nr_z[ 1]=3;   nr_z[ 2]=4;   nr_z[ 3]=5;   nr_z[ 4]=6;   nr_z[ 5]=7;
        nr_z[ 6]=8;   nr_z[ 7]=9;   nr_z[ 8]=10;  nr_z[ 9]=11;  nr_z[10]=12;  nr_z[11]=13;
        nr_z[12]=14;  nr_z[13]=15;  nr_z[14]=16;  nr_z[15]=18;  nr_z[16]=20;  nr_z[17]=22;
        nr_z[18]=24;  nr_z[19]=26;  nr_z[20]=28;  nr_z[21]=30;  nr_z[22]=32;  nr_z[23]=36;
        nr_z[24]=40;  nr_z[25]=44;  nr_z[26]=48;  nr_z[27]=52;  nr_z[28]=56;  nr_z[29]=60;
        nr_z[30]=64;  nr_z[31]=72;  nr_z[32]=80;  nr_z[33]=88;  nr_z[34]=96;  nr_z[35]=104;
        nr_z[36]=112; nr_z[37]=120; nr_z[38]=128; nr_z[39]=144; nr_z[40]=160; nr_z[41]=176;
        nr_z[42]=192; nr_z[43]=208; nr_z[44]=224; nr_z[45]=240; nr_z[46]=256; nr_z[47]=288;
        nr_z[48]=320; nr_z[49]=352; nr_z[50]=384;

        z = 0;
        // fixed-size rotators: all shifts
        for (s = 0; s < N; s = s + 1) begin
            randomize_din;
            shift = s;
            #1;
            if (s < 7)   check("barrel7",   d_b7,   7,   7,   0);
            if (s < 128) check("banyan128", d_ban,  128, 128, 0);
            check("barrel384", d_b384, N, N, 0);
            check("ibn384",    d_ibn,  N, N, 0);
        end

        // variable-size rotators: every NR lifting size, every shift
        for (zi = 0; zi < 51; zi = zi + 1) begin
            for (s = 0; s < nr_z[zi]; s = s + 1) begin
                randomize_din;
                z = nr_z[zi];
                shift = s;
                #1;
                check("qsn384", d_qsn, N, nr_z[zi], 1);
                check("rot5g",  d_5g,  N, nr_z[zi], 1);
            end
        end

        if (errors == 0) $display("PASS: %0d checks, 0 errors", checks);
        else             $display("FAIL: %0d checks, %0d lane errors", checks, errors);
        $finish;
    end
endmodule
