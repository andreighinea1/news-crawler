const dateToString = (date, yearFirst = false, withTime = true) => {
    let dateStr;
    if (yearFirst) {
        dateStr = date.getFullYear().toString() + "-" +
            (date.getMonth() + 1).toString().padStart(2, '0') + "-" +
            date.getDate().toString().padStart(2, '0');
    } else {
        dateStr = date.getDate().toString().padStart(2, '0') + "-" +
            (date.getMonth() + 1).toString().padStart(2, '0') + "-" +
            date.getFullYear().toString()
    }
    if (withTime) {
        return dateStr + ", " + date.toLocaleTimeString();
    }
    return dateStr;
}

export default dateToString