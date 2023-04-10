import { ValueRef, ValueRefView } from "./value_ref";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Index as DataIndex } from "../../core/util/templating";
import * as p from "../../core/properties";
export declare class ColorRefView extends ValueRefView {
    model: ColorRef;
    value_el?: HTMLElement;
    swatch_el?: HTMLElement;
    render(): void;
    update(source: ColumnarDataSource, i: DataIndex | null, _vars: object): void;
}
export declare namespace ColorRef {
    type Attrs = p.AttrsOf<Props>;
    type Props = ValueRef.Props & {
        hex: p.Property<boolean>;
        swatch: p.Property<boolean>;
    };
}
export interface ColorRef extends ColorRef.Attrs {
}
export declare class ColorRef extends ValueRef {
    properties: ColorRef.Props;
    __view_type__: ColorRefView;
    constructor(attrs?: Partial<ColorRef.Attrs>);
}
//# sourceMappingURL=color_ref.d.ts.map