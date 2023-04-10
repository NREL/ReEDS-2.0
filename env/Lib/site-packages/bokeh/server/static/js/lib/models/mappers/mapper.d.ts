import { Transform } from "../transforms/transform";
import { Factor } from "../ranges/factor_range";
import { Arrayable, ArrayableOf } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace Mapper {
    type Attrs = p.AttrsOf<Props>;
    type Props = Transform.Props;
}
export interface Mapper<T> extends Mapper.Attrs {
}
export declare abstract class Mapper<T> extends Transform<number, T> {
    properties: Mapper.Props;
    constructor(attrs?: Partial<Mapper.Attrs>);
    compute(_x: number): never;
    abstract v_compute(xs: ArrayableOf<number | Factor>): Arrayable<T>;
}
//# sourceMappingURL=mapper.d.ts.map