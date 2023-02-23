import ApiService from "./ApiService"

export async function getQueryHistoryApi (data) {
    return ApiService.fetchData({
        url: '/get-query-history',
        method: 'post',
        data
    })
}

export async function addQueryHistoryApi (data) {
    return ApiService.fetchData({
        url: '/add-query-history',
        method: 'post',
        data
    })
}