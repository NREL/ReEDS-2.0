export declare class LogLevel {
    readonly name: string;
    readonly level: number;
    constructor(name: string, level: number);
}
export declare class Logger {
    static TRACE: LogLevel;
    static DEBUG: LogLevel;
    static INFO: LogLevel;
    static WARN: LogLevel;
    static ERROR: LogLevel;
    static FATAL: LogLevel;
    static OFF: LogLevel;
    static log_levels: {
        [key: string]: LogLevel;
    };
    static get levels(): string[];
    static get(name: string, level?: LogLevel): Logger;
    _name: string;
    _log_level: LogLevel;
    constructor(name: string, level?: LogLevel);
    get level(): LogLevel;
    get_level(): LogLevel;
    set_level(log_level: LogLevel | string): void;
    trace(..._args: unknown[]): void;
    debug(..._args: unknown[]): void;
    info(..._args: unknown[]): void;
    warn(..._args: unknown[]): void;
    error(..._args: unknown[]): void;
}
export declare const logger: Logger;
export declare function set_log_level(level: string | LogLevel): LogLevel;
export declare function with_log_level(level: string | LogLevel, fn: () => void): void;
//# sourceMappingURL=logging.d.ts.map