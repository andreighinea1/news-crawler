import { 
    NAV_ITEM_TYPE_TITLE, 
    NAV_ITEM_TYPE_ITEM
} from 'constants/navigation.constant'

const navigationConfig = [
    {
		key: 'searchMenu',
		path: '',
		title: 'Search Menu',
		translateKey: 'nav.searchMenu.menu',
		icon: '',
		type: NAV_ITEM_TYPE_TITLE,
		authority: [],
		subMenu: [
            {
                key: 'searchMenu.searchSimilarNews',
                path: '/search-menu-similar-news',
                title: 'Search Similar News',
                translateKey: 'nav.searchMenu.searchSimilarNews',
                icon: 'searchSimilarNews',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: []
            },
            {
                key: 'searchMenu.queryHistory',
                path: '/search-menu-query-history',
                title: 'Query History',
                translateKey: 'nav.searchMenu.queryHistory',
                icon: 'queryHistory',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: []
            }
        ]
    }
]

export default navigationConfig