import { Model } from "../../../model";
import * as p from "../../../core/properties";
export declare namespace CustomJSHover {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
    };
}
export interface CustomJSHover extends CustomJSHover.Attrs {
}
export declare class CustomJSHover extends Model {
    properties: CustomJSHover.Props;
    constructor(attrs?: Partial<CustomJSHover.Attrs>);
    get values(): any[];
    _make_code(valname: string, formatname: string, varsname: string, fn: string): Function;
    format(value: any, format: string, special_vars: {
        [key: string]: unknown;
    }): string;
}
//# sourceMappingURL=customjs_hover.d.ts.map