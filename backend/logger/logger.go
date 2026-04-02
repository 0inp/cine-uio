package logger

import (
	"fmt"
	"log"
	"os"
	"strings"
)

// LogLevel represents the logging level
type LogLevel int

const (
	DEBUG LogLevel = iota
	INFO
	WARN
	ERROR
	FATAL
)

// String returns the string representation of the log level
func (l LogLevel) String() string {
	switch l {
	case DEBUG:
		return "DEBUG"
	case INFO:
		return "INFO"
	case WARN:
		return "WARN"
	case ERROR:
		return "ERROR"
	case FATAL:
		return "FATAL"
	default:
		return "UNKNOWN"
	}
}

// Logger is the main logger struct
type Logger struct {
	level  LogLevel
	logger *log.Logger
}

// NewLogger creates a new logger instance
func NewLogger(level LogLevel) *Logger {
	return &Logger{
		level:  level,
		logger: log.New(os.Stdout, "", log.LstdFlags|log.Lshortfile),
	}
}

// Debug logs a debug message
func (l *Logger) Debug(format string, v ...interface{}) {
	if l.level <= DEBUG {
		l.logger.Output(2, fmt.Sprintf("[DEBUG] "+format, v...))
	}
}

// Info logs an info message
func (l *Logger) Info(format string, v ...interface{}) {
	if l.level <= INFO {
		l.logger.Output(2, fmt.Sprintf("[INFO] "+format, v...))
	}
}

// Warn logs a warning message
func (l *Logger) Warn(format string, v ...interface{}) {
	if l.level <= WARN {
		l.logger.Output(2, fmt.Sprintf("[WARN] "+format, v...))
	}
}

// Error logs an error message
func (l *Logger) Error(format string, v ...interface{}) {
	if l.level <= ERROR {
		l.logger.Output(2, fmt.Sprintf("[ERROR] "+format, v...))
	}
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(format string, v ...interface{}) {
	if l.level <= FATAL {
		l.logger.Output(2, fmt.Sprintf("[FATAL] "+format, v...))
	}
	os.Exit(1)
}

// ParseLogLevel parses a string log level into a LogLevel
func ParseLogLevel(level string) LogLevel {
	switch strings.ToUpper(level) {
	case "DEBUG":
		return DEBUG
	case "INFO":
		return INFO
	case "WARN":
		return WARN
	case "ERROR":
		return ERROR
	case "FATAL":
		return FATAL
	default:
		return INFO // Default to INFO
	}
}
