import React, {useCallback, useEffect, useRef, useState} from 'react'
import {Button, Input} from 'components/ui'
import {DataTable} from 'components/shared'
import debounce from 'lodash/debounce'
import axios from 'axios'
import appConfig from 'configs/app.config'
import {useSelector} from "react-redux";
import {useNavigate} from "react-router-dom";
import sortBy from "../../utils/sortBy";

const {apiPrefix} = appConfig


// TODO-BUG: Table with 27 items, page 2 selected, 25 / page -> switch to 100 / page => EXPECTED to switch to the last ok (page 1)
// TODO: Add the SubComponent to the table rows


const NewsQueryHistory = () => {

    const [data, setData] = useState([])
    const [loading, setLoading] = useState(false)
    const [tableData, setTableData] = useState(
        {
            total: 0,
            pageIndex: 1,
            pageSize: 10,
            query: '',
            sort: {
                order: '',
                key: ''
            }
        }
    )

    const uid = useSelector((state) => state.auth.user.uid)
    let navigate = useNavigate();

    const inputRef = useRef()

    const debounceFn = useCallback(debounce(handleDebounceFn, 500), [])

    function handleDebounceFn(val) {
        if (typeof val === 'string' && (val.length > 1 || val.length === 0)) {
            setTableData(prevData => ({...prevData, ...{query: val, pageIndex: 1}}))
        }
    }

    const handleChange = (e) => {
        debounceFn(e.target.value)
    }


    const handleSearchedArticles = (cellProps) => {
        navigate("/news-query-result", {
            replace: true,
            state: {searchedArticles: cellProps.cell.value.searchedArticles}
        });
    }


    const handleSeeClusters = (cellProps) => {
        navigate("/news-clusters-result", {
            replace: true,
            state: {formedClusters: cellProps.cell.value.formedClusters}
        });
    }


    const handleSimilarNews = (cellProps) => {
        navigate("/similar-news-result", {
            replace: true,
            state: {similarNews: cellProps.cell.value.similarNews}
        });
    }

    const columns = [
        {
            Header: 'URL/Title',
            accessor: 'url',
            sortable: true,
        },
        {
            Header: 'Date',
            accessor: 'date',
            sortable: true,
        },
        {
            Header: 'Count',
            accessor: 'articlesCount',
            sortable: true,
        },
        {
            Header: '',
            id: 'action',
            accessor: (row) => row,
            Cell: props => <Button size="xs" onClick={() => handleSearchedArticles(props)}>See Details</Button>
        },
        {
            Header: '',
            id: 'clusters',
            accessor: (row) => row,
            Cell: props => <Button size="xs" onClick={() => handleSeeClusters(props)}>See Clusters</Button>
        },
        {
            Header: '',
            id: 'similarity',
            accessor: (row) => row,
            Cell: props => <Button size="xs" onClick={() => handleSimilarNews(props)}>See Similar News</Button>
        },
    ]

    const handlePaginationChange = pageIndex => {
        setTableData(prevData => ({...prevData, ...{pageIndex}}))
    }

    const handleSelectChange = pageSize => {
        setTableData(prevData => ({...prevData, ...{pageSize}}))
    }

    const handleSort = ({order, key}, aaa) => {
        // console.log({order, key})
        // console.log(aaa)
        setTableData(prevData => ({...prevData, ...{sort: {order, key}}}))
    }

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            const response = await axios.post(`${apiPrefix}/get-query-history`, {uid, tableData})
            if (response.data) {
                const data = response.data.data;

                try {
                    data.forEach(article => {
                        article.dateSortId = Date.parse(article.publishedAt)  // Used for sorting
                        article.articlesCount = article.searchedArticles.length  // Just a count of articles
                    })
                    if (tableData.sort.key !== '' && tableData.sort.order !== '') {
                        data.sort(sortBy(
                            tableData.sort.key,
                            tableData.sort.order === 'desc',
                            null,
                            false)
                        )
                    }
                } catch (e) {
                    console.log(data)


                    data.forEach(article => {
                        article.dateSortId = Date.parse(article.publishedAt)  // Used for sorting
                        article.articlesCount = article.searchedArticles.length  // Just a count of articles
                    })
                }

                setData(data);
                setLoading(false);
                setTableData(prevData => ({...prevData, ...{total: response.data.total}}));
            }
        }
        fetchData()
    }, [tableData.pageIndex, tableData.sort, tableData.pageSize, tableData.query])

    return (
        <>
            <div className="flex justify-end mb-4">
                <Input
                    ref={inputRef}
                    placeholder="Search..."
                    size="sm"
                    className="lg:w-52"
                    onChange={handleChange}
                />
            </div>
            <DataTable
                columns={columns}
                data={data}
                loading={loading}
                pagingData={tableData}
                onPaginationChange={handlePaginationChange}
                onSelectChange={handleSelectChange}
                onSort={handleSort}
            />
        </>
    )
}

export default NewsQueryHistory