import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Expression } from "./expression";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace CumSum {
    type Attrs = p.AttrsOf<Props>;
    type Props = Expression.Props & {
        field: p.Property<string>;
        include_zero: p.Property<boolean>;
    };
}
export interface CumSum extends CumSum.Attrs {
}
export declare class CumSum extends Expression {
    properties: CumSum.Props;
    constructor(attrs?: Partial<CumSum.Attrs>);
    protected _v_compute(source: ColumnarDataSource): Arrayable<number>;
}
//# sourceMappingURL=cumsum.d.ts.map