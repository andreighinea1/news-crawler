import {createServer} from 'miragejs'
import appConfig from 'configs/app.config'

import {signInUserData} from './data/authData'
import {queryHistoryData} from "./data/queryHistoryData";

import {authFakeApi} from './fakeApi'
import {queryHistoryFakeApi} from "./historyFakeApi";

const {apiPrefix} = appConfig

export default function mockServer({environment = 'test'}) {
    const server = createServer({
        environment,
        seeds(server) {
            // https://stackoverflow.com/a/73888870
            const dbData = localStorage.getItem('db');
            if (dbData) {
                // https://miragejs.com/api/classes/db/#load-data
                server.db.loadData(JSON.parse(dbData));
            } else {
                server.db.loadData({
                    signInUserData,
                    queryHistoryData
                })
            }
        },
        routes() {
            this.urlPrefix = ''
            this.namespace = ''
            this.passthrough(request => {
                let isExternal = request.url.startsWith('http')
                return isExternal
            })
            this.passthrough()


            authFakeApi(this, apiPrefix)
            queryHistoryFakeApi(this, apiPrefix)
        },
    });

    // https://stackoverflow.com/a/73888870
    // https://miragejs.com/api/classes/server/#pretender
    server.pretender.handledRequest = function (verb) {
        if (verb.toLowerCase() !== 'get' && verb.toLowerCase() !== 'head') {
            localStorage.setItem('db', JSON.stringify(server.db.dump()));
        }
    };

    // localStorage.removeItem('db');

    return server;
}