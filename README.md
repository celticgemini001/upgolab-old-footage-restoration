# Restoring Old Family Video Without a Workstation

Old footage fails in four separate layers, measured. Deinterlace/denoise order barely matters (0.8%), hqdn3d peaks at spatial 32 then reverses, nlmeans cuts 78.5% of sigma-10 noise, sharpening a blocked frame raises blockiness 12.7%, 60% of a 59.94 fps file is duplicate frames saving 20% compute but 0% bitrate. Deinterlacers split by 7.7 dB on invented rows while weave wins PSNR and carries 266x the comb, and deinterlacing before the upscale is worth 0.6 dB against a 21% encode-cost difference.

**Read it with the tables and the reproduction snippets:** <https://celticgemini001.github.io/upgolab-old-footage-restoration/>

## About this repo

This repository exists to serve one measured article. Every number in it came from
ffmpeg and numpy run on real files on this machine — the commands are in the page so
you can re-run them and get the same rows. Where the measurement contradicted the
hypothesis, the page says so.

## The tool behind the notes

<https://upgolab.com> — browser-based AI upscaler for photos and short video.

## Index

All the guides are cross-linked from the hub:
<https://celticgemini001.github.io/upgolab-tools/>
