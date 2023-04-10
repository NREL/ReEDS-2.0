import { ReglWrapper } from "./regl_wrap";
import { LineCap, LineJoin } from "../../../core/enums";
import { HatchPattern } from "../../../core/property_mixins";
import { uint32 } from "../../../core/types";
import { Uniform } from "../../../core/uniforms";
import { AttributeConfig, Buffer } from "regl";
type WrappedArrayType = Float32Array | Uint8Array;
declare abstract class WrappedBuffer<ArrayType extends WrappedArrayType> {
    protected regl_wrapper: ReglWrapper;
    protected buffer?: Buffer;
    protected array?: ArrayType;
    protected is_scalar: boolean;
    constructor(regl_wrapper: ReglWrapper);
    get_sized_array(length: number): ArrayType;
    protected is_normalized(): boolean;
    get length(): number;
    protected abstract new_array(len: number): ArrayType;
    set_from_array(numbers: number[] | Float32Array): void;
    set_from_prop(prop: Uniform<number>, length_if_scalar?: number): void;
    set_from_scalar(scalar: number, length_if_scalar?: number): void;
    to_attribute_config(offset?: number): AttributeConfig;
    update(is_scalar?: boolean): void;
}
export declare class Float32Buffer extends WrappedBuffer<Float32Array> {
    protected new_array(len: number): Float32Array;
}
export declare class Uint8Buffer extends WrappedBuffer<Uint8Array> {
    protected new_array(len: number): Uint8Array;
    set_from_color(color_prop: Uniform<uint32>, alpha_prop: Uniform<number>, length_if_scalar?: number): void;
    set_from_hatch_pattern(hatch_pattern_prop: Uniform<HatchPattern>, length_if_scalar?: number): void;
    set_from_line_cap(line_cap_prop: Uniform<LineCap>, length_if_scalar?: number): void;
    set_from_line_join(line_join_prop: Uniform<LineJoin>, length_if_scalar?: number): void;
}
export declare class NormalizedUint8Buffer extends Uint8Buffer {
    protected is_normalized(): boolean;
}
export {};
//# sourceMappingURL=buffer.d.ts.map