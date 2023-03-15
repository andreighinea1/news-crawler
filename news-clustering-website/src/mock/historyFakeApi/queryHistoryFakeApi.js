import {Response} from 'miragejs'
import uniqueId from "lodash/uniqueId";
import paginate from "../../utils/paginate";
import dateToString from "../../utils/dateToString";


export default function queryHistoryFakeApi(server, apiPrefix) {

    server.post(`${apiPrefix}/add-query-history`, (schema, {requestBody}) => {
        const {uid, url, searchedArticles} = JSON.parse(requestBody)

        const newQueryHistoryEntry = {
            uid,
            url,
            searchedArticles,
            date: dateToString(new Date())
        }

        schema.db.queryHistoryData.insert({...newQueryHistoryEntry, ...{id: uniqueId('query_')}})
        return {
            newQueryHistoryEntry,
            token: 'wVYrxaeNa9OxdnULvde1Au5m5w63'
        }
    })

    server.post(`${apiPrefix}/get-query-history`, (schema, {requestBody}) => {
        const {uid, tableData} = JSON.parse(requestBody)
        // console.log('tableData', tableData)  // TODO: Use tableData to implement sorting somehow

        const userCompleteQueryHistory = schema.db.queryHistoryData.where({uid})
        if (userCompleteQueryHistory) {
            return {
                data: paginate(userCompleteQueryHistory, tableData.pageSize, tableData.pageIndex),
                total: userCompleteQueryHistory.length
            }
        }
        return new Response(401, {some: 'header'}, {message: `Unknown error`})
    })

}