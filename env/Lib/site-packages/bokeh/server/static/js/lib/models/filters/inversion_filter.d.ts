import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace InversionFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        operand: p.Property<Filter>;
    };
}
export interface InversionFilter extends InversionFilter.Attrs {
}
export declare class InversionFilter extends Filter {
    properties: InversionFilter.Props;
    constructor(attrs?: Partial<InversionFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=inversion_filter.d.ts.map