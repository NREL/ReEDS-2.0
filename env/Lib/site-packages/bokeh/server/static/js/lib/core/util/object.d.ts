import { PlainObject, Arrayable } from "../types";
export declare const keys: {
    (o: object): string[];
    (o: {}): string[];
}, values: {
    <T>(o: {
        [s: string]: T;
    } | ArrayLike<T>): T[];
    (o: {}): any[];
}, entries: {
    <T>(o: {
        [s: string]: T;
    } | ArrayLike<T>): [string, T][];
    (o: {}): [string, any][];
}, assign: {
    <T extends {}, U>(target: T, source: U): T & U;
    <T_1 extends {}, U_1, V>(target: T_1, source1: U_1, source2: V): T_1 & U_1 & V;
    <T_2 extends {}, U_2, V_1, W>(target: T_2, source1: U_2, source2: V_1, source3: W): T_2 & U_2 & V_1 & W;
    (target: object, ...sources: any[]): any;
}, to_object: {
    <T = any>(entries: Iterable<readonly [PropertyKey, T]>): {
        [k: string]: T;
    };
    (entries: Iterable<readonly any[]>): any;
};
export declare const extend: {
    <T extends {}, U>(target: T, source: U): T & U;
    <T_1 extends {}, U_1, V>(target: T_1, source1: U_1, source2: V): T_1 & U_1 & V;
    <T_2 extends {}, U_2, V_1, W>(target: T_2, source1: U_2, source2: V_1, source3: W): T_2 & U_2 & V_1 & W;
    (target: object, ...sources: any[]): any;
};
export declare function fields<T extends object>(obj: T): (keyof T)[];
export declare function clone<T>(obj: PlainObject<T>): PlainObject<T>;
export declare function merge<T>(obj1: PlainObject<Arrayable<T>>, obj2: PlainObject<Arrayable<T>>): PlainObject<T[]>;
export declare function size(obj: PlainObject): number;
export declare function is_empty(obj: PlainObject): boolean;
export declare class Dict<V> implements Map<string, V> {
    readonly obj: {
        [key: string]: V;
    };
    constructor(obj: {
        [key: string]: V;
    });
    readonly [Symbol.toStringTag] = "Dict";
    clear(): void;
    delete(key: string): boolean;
    get(key: string): V | undefined;
    has(key: string): boolean;
    set(key: string, value: V): this;
    get size(): number;
    get is_empty(): boolean;
    [Symbol.iterator](): IterableIterator<[string, V]>;
    keys(): IterableIterator<string>;
    values(): IterableIterator<V>;
    entries(): IterableIterator<[string, V]>;
    forEach(callback: (value: V, key: string, map: Map<string, V>) => void, that?: unknown): void;
}
export declare function dict<V>(o: {
    [key: string]: V;
}): Dict<V>;
//# sourceMappingURL=object.d.ts.map