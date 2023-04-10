import { Signal0 } from "./signaling";
import type { HasProps } from "./has_props";
import * as enums from "./enums";
import { Arrayable, IntArray, FloatArray, TypedArray, ColorArray, uint32 } from "./types";
import * as types from "./types";
import { Factor } from "../models/ranges/factor_range";
import { ColumnarDataSource } from "../models/sources/columnar_data_source";
import { /*Value,*/ Scalar, Vector, Dimensional } from "./vectorization";
import { Kind } from "./kinds";
import { NDArray } from "./util/ndarray";
import { Uniform, UniformScalar, UniformVector, ColorUniformVector } from "./uniforms";
export { Uniform, UniformScalar, UniformVector };
export declare function isSpec(obj: any): boolean;
export interface Theme {
    get(obj: HasProps | typeof HasProps, attr: string): unknown;
}
export declare function use_theme(theme?: Theme | null): void;
export type UniformsOf<M> = {
    [K in keyof M]: M[K] extends VectorSpec<infer T, any> ? Uniform<T> : M[K] extends ScalarSpec<infer T, any> ? UniformScalar<T> : M[K] extends Property<infer T> ? T : never;
};
export type AttrsOf<P> = {
    [K in keyof P]: P[K] extends Property<infer T> ? T : never;
};
export type DefineOf<P, HP extends HasProps = HasProps> = {
    [K in keyof P]: P[K] extends Property<infer T> ? [PropertyConstructor<T> | PropertyAlias | Kind<T>, (Unset | T | ((obj: HP) => T))?, PropertyOptions<T>?] : never;
};
export type DefaultsOf<P> = {
    [K in keyof P]: P[K] extends Property<infer T> ? T | ((obj: HasProps) => T) : never;
};
export type PropertyOptions<T> = {
    internal?: boolean;
    readonly?: boolean;
    convert?(value: T): T | undefined;
    on_update?(value: T, obj: HasProps): void;
};
export interface PropertyConstructor<T> {
    new (obj: HasProps, attr: string, kind: Kind<T>, default_value: (obj: HasProps) => T, options?: PropertyOptions<T>): Property<T>;
    readonly prototype: Property<T>;
}
export declare const unset: unique symbol;
export type Unset = typeof unset;
export declare class UnsetValueError extends Error {
}
export declare abstract class Property<T = unknown> {
    readonly obj: HasProps;
    readonly attr: string;
    readonly kind: Kind<T>;
    readonly default_value: (obj: HasProps) => T;
    __value__: T;
    get syncable(): boolean;
    protected _value: T | Unset;
    get is_unset(): boolean;
    protected _initialized: boolean;
    get initialized(): boolean;
    initialize(initial_value?: T | Unset): void;
    get_value(): T;
    set_value(val: T): void;
    _default_override(): T | Unset;
    private _dirty;
    get dirty(): boolean;
    readonly change: Signal0<HasProps>;
    internal: boolean;
    readonly: boolean;
    convert?(value: T): T | undefined;
    on_update?(value: T, obj: HasProps): void;
    constructor(obj: HasProps, attr: string, kind: Kind<T>, default_value: (obj: HasProps) => T, options?: PropertyOptions<T>);
    protected _update(attr_value: T): void;
    toString(): string;
    normalize(values: any): any;
    validate(value: unknown): void;
    valid(value: unknown): boolean;
}
export declare class PropertyAlias {
    readonly attr: string;
    constructor(attr: string);
}
export declare function Alias(attr: string): PropertyAlias;
export declare class PrimitiveProperty<T> extends Property<T> {
}
export declare class Font extends PrimitiveProperty<string> {
    _default_override(): string | Unset;
}
export declare class ScalarSpec<T, S extends Scalar<T> = Scalar<T>> extends Property<T | S> {
    __value__: T;
    __scalar__: S;
    protected _value: this["__scalar__"] | Unset;
    get_value(): S;
    protected _update(attr_value: S | T): void;
    materialize(value: T): T;
    scalar(value: T, n: number): UniformScalar<T>;
    uniform(source: ColumnarDataSource): UniformScalar<T>;
}
export declare class AnyScalar extends ScalarSpec<any> {
}
export declare class ColorScalar extends ScalarSpec<types.Color | null> {
}
export declare class NumberScalar extends ScalarSpec<number> {
}
export declare class StringScalar extends ScalarSpec<string> {
}
export declare class NullStringScalar extends ScalarSpec<string | null> {
}
export declare class ArrayScalar extends ScalarSpec<any[]> {
}
export declare class LineJoinScalar extends ScalarSpec<enums.LineJoin> {
}
export declare class LineCapScalar extends ScalarSpec<enums.LineCap> {
}
export declare class LineDashScalar extends ScalarSpec<enums.LineDash | number[]> {
}
export declare class FontScalar extends ScalarSpec<string> {
    _default_override(): string | Unset;
}
export declare class FontSizeScalar extends ScalarSpec<string> {
}
export declare class FontStyleScalar extends ScalarSpec<enums.FontStyle> {
}
export declare class TextAlignScalar extends ScalarSpec<enums.TextAlign> {
}
export declare class TextBaselineScalar extends ScalarSpec<enums.TextBaseline> {
}
export declare abstract class VectorSpec<T, V extends Vector<T> = Vector<T>> extends Property<T | V> {
    __value__: T;
    __vector__: V;
    protected _value: this["__vector__"] | Unset;
    get_value(): V;
    protected _update(attr_value: V | T): void;
    materialize(value: T): T;
    v_materialize(values: Arrayable<T>): Arrayable<T>;
    scalar(value: T, n: number): UniformScalar<T>;
    vector(values: Arrayable<T>): UniformVector<T>;
    uniform(source: ColumnarDataSource): Uniform<T>;
    array(source: ColumnarDataSource): Arrayable<unknown>;
}
export declare abstract class DataSpec<T> extends VectorSpec<T> {
}
export declare abstract class UnitsSpec<T, Units> extends VectorSpec<T, Dimensional<Vector<T>, Units>> {
    abstract get default_units(): Units;
    abstract get valid_units(): Units[];
    protected _value: this["__vector__"] | Unset;
    _update(attr_value: any): void;
    get units(): Units;
    set units(units: Units);
}
export declare abstract class NumberUnitsSpec<Units> extends UnitsSpec<number, Units> {
    array(source: ColumnarDataSource): FloatArray;
}
export declare abstract class BaseCoordinateSpec<T> extends DataSpec<T> {
    abstract get dimension(): "x" | "y";
}
export declare abstract class CoordinateSpec extends BaseCoordinateSpec<number | Factor> {
}
export declare abstract class CoordinateSeqSpec extends BaseCoordinateSpec<Arrayable<number> | Arrayable<Factor>> {
}
export declare abstract class CoordinateSeqSeqSeqSpec extends BaseCoordinateSpec<number[][][] | Factor[][][]> {
}
export declare class XCoordinateSpec extends CoordinateSpec {
    readonly dimension = "x";
}
export declare class YCoordinateSpec extends CoordinateSpec {
    readonly dimension = "y";
}
export declare class XCoordinateSeqSpec extends CoordinateSeqSpec {
    readonly dimension = "x";
}
export declare class YCoordinateSeqSpec extends CoordinateSeqSpec {
    readonly dimension = "y";
}
export declare class XCoordinateSeqSeqSeqSpec extends CoordinateSeqSeqSeqSpec {
    readonly dimension = "x";
}
export declare class YCoordinateSeqSeqSeqSpec extends CoordinateSeqSeqSeqSpec {
    readonly dimension = "y";
}
export declare class AngleSpec extends NumberUnitsSpec<enums.AngleUnits> {
    get default_units(): enums.AngleUnits;
    get valid_units(): enums.AngleUnits[];
    materialize(value: number): number;
    v_materialize(values: Arrayable<number>): Float32Array;
    array(_source: ColumnarDataSource): Float32Array;
}
export declare class DistanceSpec extends NumberUnitsSpec<enums.SpatialUnits> {
    get default_units(): enums.SpatialUnits;
    get valid_units(): enums.SpatialUnits[];
}
export declare class NullDistanceSpec extends DistanceSpec {
    materialize(value: number | null): number;
}
export declare class BooleanSpec extends DataSpec<boolean> {
    v_materialize(values: Arrayable<boolean>): Arrayable<boolean>;
    array(source: ColumnarDataSource): Uint8Array;
}
export declare class IntSpec extends DataSpec<number> {
    v_materialize(values: Arrayable<number>): TypedArray;
    array(source: ColumnarDataSource): IntArray;
}
export declare class NumberSpec extends DataSpec<number> {
    v_materialize(values: Arrayable<number>): TypedArray;
    array(source: ColumnarDataSource): FloatArray;
}
export declare class ScreenSizeSpec extends NumberSpec {
    valid(value: unknown): boolean;
}
export declare class ColorSpec extends DataSpec<types.Color | null> {
    materialize(color: types.Color | null): uint32;
    v_materialize(colors: Arrayable<types.Color | null> | NDArray): ColorArray;
    protected _from_css_array(colors: Arrayable<types.Color | null>): ColorArray;
    vector(values: ColorArray): ColorUniformVector;
}
export declare class NDArraySpec extends DataSpec<NDArray> {
}
export declare class AnySpec extends DataSpec<any> {
}
export declare class StringSpec extends DataSpec<string> {
}
export declare class NullStringSpec extends DataSpec<string | null> {
}
export declare class ArraySpec extends DataSpec<any[]> {
}
export declare class MarkerSpec extends DataSpec<enums.MarkerType> {
}
export declare class LineJoinSpec extends DataSpec<enums.LineJoin> {
}
export declare class LineCapSpec extends DataSpec<enums.LineCap> {
}
export declare class LineDashSpec extends DataSpec<enums.LineDash | number[]> {
}
export declare class FontSpec extends DataSpec<string> {
    _default_override(): string | Unset;
}
export declare class FontSizeSpec extends DataSpec<string> {
}
export declare class FontStyleSpec extends DataSpec<enums.FontStyle> {
}
export declare class TextAlignSpec extends DataSpec<enums.TextAlign> {
}
export declare class TextBaselineSpec extends DataSpec<enums.TextBaseline> {
}
//# sourceMappingURL=properties.d.ts.map