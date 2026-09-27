package com.bintang.vivofastboot;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Small AVB helper matching AOSP fastboot's disable-verity/verification flags. */
public final class AvbUtils {
    private AvbUtils() {}

    public static byte[] readAll(InputStream in, long maxBytes) throws IOException, FastbootException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[64 * 1024];
        long total = 0;
        int n;
        while ((n = in.read(buf)) != -1) {
            total += n;
            if (total > maxBytes) throw new FastbootException("File exceeds fastboot download limit");
            out.write(buf, 0, n);
        }
        return out.toByteArray();
    }

    public static void patchDisableFlags(byte[] data, boolean disableVerity, boolean disableVerification)
            throws FastbootException {
        if ((!disableVerity && !disableVerification)) return;
        if (data == null || data.length < 256) throw new FastbootException("vbmeta image is smaller than 256 bytes");

        long offset = findVbmetaOffset(data);
        if (offset < 0 || offset + 124 > data.length) {
            throw new FastbootException("No valid AVB0 vbmeta header found");
        }

        int flagsLastByte = (int) offset + 123;
        if (disableVerity) data[flagsLastByte] = (byte) ((data[flagsLastByte] & 0xFF) | 0x01);
        if (disableVerification) data[flagsLastByte] = (byte) ((data[flagsLastByte] & 0xFF) | 0x02);
    }

    private static long findVbmetaOffset(byte[] data) {
        if (hasMagic(data, 0, "AVB0")) return 0;

        // AVB footer is 64 bytes at the end of a non-sparse AVB image.
        if (data.length >= 64 && hasMagic(data, data.length - 64, "AVBf")) {
            long off = readBigEndianLong(data, data.length - 64 + 20);
            if (off >= 0 && off <= data.length - 256 && hasMagic(data, (int) off, "AVB0")) {
                return off;
            }
        }
        return -1;
    }

    private static boolean hasMagic(byte[] data, int off, String magic) {
        byte[] m = magic.getBytes(StandardCharsets.US_ASCII);
        if (off < 0 || off + m.length > data.length) return false;
        for (int i = 0; i < m.length; i++) if (data[off + i] != m[i]) return false;
        return true;
    }

    private static long readBigEndianLong(byte[] data, int off) {
        long v = 0;
        for (int i = 0; i < 8; i++) v = (v << 8) | (data[off + i] & 0xFFL);
        return v;
    }
}
