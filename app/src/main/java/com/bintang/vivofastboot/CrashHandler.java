package com.bintang.vivofastboot;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class CrashHandler {
    public interface Listener {
        void onCrash(String report);
    }

    private CrashHandler() {}

    public static void install(Context context, Listener listener) {
        Context app = context.getApplicationContext();
        SharedPreferences prefs = app.getSharedPreferences("crash", Context.MODE_PRIVATE);
        Thread.setDefaultUncaughtExceptionHandler((thread, throwable) -> {
            String report = buildReport(thread, throwable);
            prefs.edit().putString("last_report", report).apply();
            Log.e("VivoFastboot", report, throwable);
            new Handler(Looper.getMainLooper()).post(() -> {
                if (listener != null) listener.onCrash(report);
            });
            // Intentionally do not call Android's old uncaught-exception handler here.
            // Recoverable action errors are caught separately in MainActivity.
            // This handler is a last-resort display/logging path.
        });
    }

    public static String takeLastReport(Context context) {
        SharedPreferences prefs = context.getSharedPreferences("crash", Context.MODE_PRIVATE);
        String report = prefs.getString("last_report", "");
        prefs.edit().remove("last_report").apply();
        return report;
    }

    private static String buildReport(Thread thread, Throwable t) {
        StringWriter sw = new StringWriter();
        t.printStackTrace(new PrintWriter(sw));
        String now = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(new Date());
        return "=== VIVOFASTBOOT CRASH ===\n" +
                "Time: " + now + "\n" +
                "Thread: " + thread.getName() + "\n" +
                sw + "\n";
    }
}
