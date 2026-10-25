// buusdo Phase-3 PoC — SDR→HDR display-color tone map stub (HLSL)
// NOT applied to DWM at runtime. Research / offline compile only.
// Requires BUUSDO_ENABLE_DWM_HDR_PROTOTYPE=1 to materialize beside a game dir.

cbuffer BuusdoHdrParams : register(b0)
{
    float PeakNits;      // e.g. 400–1000
    float PaperWhite;    // SDR reference white in nits
    float ContrastBoost; // mild midtone lift
    float _pad;
};

Texture2D SdrSource : register(t0);
SamplerState LinearClamp : register(s0);

float3 ExpandSdrToLinear(float3 sdr)
{
    // Approximate sRGB EOTF (simplified).
    return pow(saturate(sdr), 2.2);
}

float3 ToneMapToHdr(float3 linearSdr)
{
    float3 mapped = linearSdr * (PaperWhite / 80.0);
    mapped = mapped * (1.0 + ContrastBoost * (1.0 - mapped));
    return min(mapped, PeakNits / 80.0);
}

float4 MainPS(float2 uv : TEXCOORD0) : SV_Target
{
    float3 sdr = SdrSource.Sample(LinearClamp, uv).rgb;
    float3 linearSdr = ExpandSdrToLinear(sdr);
    float3 hdr = ToneMapToHdr(linearSdr);
    return float4(hdr, 1.0);
}
