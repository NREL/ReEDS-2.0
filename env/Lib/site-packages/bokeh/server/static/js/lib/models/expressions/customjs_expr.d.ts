import { Expression } from "./expression";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import * as p from "../../core/properties";
import { Arrayable } from "../../core/types";
export declare namespace CustomJSExpr {
    type Attrs = p.AttrsOf<Props>;
    type Props = Expression.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
    };
}
export interface CustomJSExpr extends CustomJSExpr.Attrs {
}
export declare class CustomJSExpr extends Expression {
    properties: CustomJSExpr.Props;
    constructor(attrs?: Partial<CustomJSExpr.Attrs>);
    connect_signals(): void;
    get names(): string[];
    get values(): unknown[];
    get func(): GeneratorFunction;
    protected _v_compute(source: ColumnarDataSource): Arrayable<unknown>;
}
//# sourceMappingURL=customjs_expr.d.ts.map