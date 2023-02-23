import {Response} from 'miragejs'
import uniqueId from 'lodash/uniqueId'
import isEmpty from 'lodash/isEmpty'

export default function authFakeApi(server, apiPrefix) {

    server.post(`${apiPrefix}/sign-in`, (schema, {requestBody}) => {
        const {userName, password} = JSON.parse(requestBody)
        const user = schema.db.signInUserData.findBy({userName, password})
        // console.log('user', user)
        if (user) {
            const {uid, avatar, name, email, authority} = user
            return {
                user: {uid, avatar, name, email, authority},
                token: 'wVYrxaeNa9OxdnULvde1Au5m5w63'
            }
        }
        return new Response(401, {some: 'header'}, {message: `userName: admin | password: 123Qwe`})
    })

    server.post(`${apiPrefix}/sign-out`, () => {
        return true
    })

    server.post(`${apiPrefix}/sign-up`, (schema, {requestBody}) => {
        const {name, userName, password, email} = JSON.parse(requestBody)
        const userExist = schema.db.signInUserData.findBy({userName})
        const emailUsed = schema.db.signInUserData.findBy({email})
        const newUser = {
            uid: uniqueId('user_'),
            avatar: '/img/avatars/thumb-1.jpg',
            name,
            email,
            authority: ['admin', 'user'],
        }
        if (!isEmpty(userExist)) {
            const errors = [
                {message: '', domain: "global", reason: "invalid"}
            ]
            return new Response(400, {some: 'header'}, {errors, message: 'User already exist!'})
        }

        if (!isEmpty(emailUsed)) {
            const errors = [
                {message: '', domain: "global", reason: "invalid"}
            ]
            return new Response(400, {some: 'header'}, {errors, message: 'Email already used'})
        }

        schema.db.signInUserData.insert({...newUser, ...{password, userName}})
        return {
            user: newUser,
            token: 'wVYrxaeNa9OxdnULvde1Au5m5w63'
        }
    })

    server.post(`${apiPrefix}/forgot-password`, () => {
        return true
    })

    server.post(`${apiPrefix}/reset-password`, () => {
        return true
    })
}