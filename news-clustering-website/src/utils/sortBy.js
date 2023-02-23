const sortPrimer = (key) => {
    if (typeof key === 'string' || key instanceof String) {
        return key.toLowerCase();
    }
    return key;
}

const sortBy = (field, reverse, primer, caseSensitive = true) => {
    if (!caseSensitive && !primer) {
        primer = sortPrimer;
    }

    const key = primer ? function (x) {
        return primer(x[field])
    } : function (x) {
        return x[field]
    }

    reverse = !reverse ? 1 : -1
    return function (a, b) {
        // eslint-disable-next-line no-sequences
        return a = key(a), b = key(b), reverse * ((a > b) - (b > a))
    }
}

export default sortBy