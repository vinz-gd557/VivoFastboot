package com.bintang.vivofastboot;

public class FastbootException extends Exception {
    public FastbootException(String message) {
        super(message);
    }

    public FastbootException(String message, Throwable cause) {
        super(message, cause);
    }
}
