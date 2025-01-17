import React, { useState, useEffect } from 'react';
import _ from 'lodash';
import intl from 'react-intl-universal';
import { useHistory } from 'react-router-dom';
import { Button, Table, message } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

import servicesKnowledgeNetwork from '@/services/knowledgeNetwork';

import Format from '@/components/Format';
import AvatarName from '@/components/Avatar';
import IconFont from '@/components/IconFont';
import SearchInput from '@/components/SearchInput';

import CreateModal from './createModal';
import DeleteModal from './deleteModal';

import NoResult from '@/assets/images/noResult.svg';
import addContentImg from '@/assets/images/create.svg';
import './index.less';

const ERROR_CODE: any = {
  'Builder.service.knw_service.knwService.getKnw.RequestError': 'graphList.getListError', // 查询错误
  'Builder.controller.knowledgeNetwork_controller.getAllKnw.PermissionError': 'graphList.permissionError' // 权限错误
};
const indicator = <LoadingOutlined style={{ fontSize: 24, color: '#54639c', top: '200px' }} spin />;

const GraphList = () => {
  const history = useHistory();

  const [loading, setLoading] = useState(false);
  const [tableData, setTableData] = useState([]);
  const [sorter, setSorter] = useState({ rule: 'update', order: 'desc' });
  const [pagination, setPagination] = useState({ size: 10, total: 0, page: 1 });
  const [searchValue, setSearchValue] = useState('');
  const [selectKey, setSelectKey] = useState(0);
  const [delId, setDelId] = useState(0);
  const [createOrEditData, setCreateOrEditData] = useState<any>({});
  const { size, total, page } = pagination;

  useEffect(() => {
    document.title = ` ${intl.get('graphList.mygraph')}_AnyDATA`;
    getData(sorter.rule, sorter.order);
  }, [page, sorter.rule, sorter.order]);

  /**
   *获取列表数据
   */
  const getData = async (rule: string, order: string) => {
    setLoading(true);
    try {
      const { res = {}, ErrorCode = '' } = await servicesKnowledgeNetwork.knowledgeNetGet({ size, page, rule, order });
      if (res?.df) {
        setTableData(res?.df);
        setPagination({ ...pagination, total: res?.count });
      }
      if (ERROR_CODE?.[ErrorCode]) message.error(intl.get(ERROR_CODE[ErrorCode]));

      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  };
  const onRefreshList = () => getData(sorter.rule, sorter.order);

  // 点击进入知识网络
  const onToPageNetwork = (id: string | number) => history.push(`/knowledge/network?id=${id}`);

  /**
   * 当前页面变化
   */
  const currentChange = (page: number) => {
    setPagination({ ...pagination, page });
  };

  /**
   * 表格排序
   */
  const sortOrderChange = (pagination: any, filters: any, sorter: any) => {
    const order = sorter.order === 'descend' ? 'desc' : 'asc';
    const rule = sorter.field === 'creation_time' ? 'create' : 'update';
    setSorter({ rule, order });
  };

  /**
   * 搜索
   */
  const onSearch = async (value: string) => {
    const { size } = pagination;
    const knw_name = value;

    setLoading(true);
    setSearchValue(value);

    try {
      const data = { knw_name, size, page, rule: sorter.rule, order: sorter.order };
      const { res = {}, ErrorCode = '' } = await servicesKnowledgeNetwork.knowledgeNetGetByName(data);

      if (res?.df) {
        setTableData(res?.df);
        setPagination({ ...pagination, total: res?.count });
      }

      if (ERROR_CODE?.[ErrorCode]) message.error(intl.get(ERROR_CODE[ErrorCode]));

      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  };

  /**
   * 同步搜索的值
   */
  const searchChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (!e?.target?.value) return;
    setSearchValue(e?.target?.value);
  };

  // 删除弹窗操作
  const onOpenDelete = (item: any) => setDelId(item.id);
  const onCloseDelete = () => setDelId(0);

  // 创建或者编辑弹窗操作
  const onOpenCreateOrEdit = (data = {}) => {
    const type = _.isEmpty(data) ? 'add' : 'edit';
    setCreateOrEditData({ type, data });
  };
  const onCloseCreateOrEdit = () => setCreateOrEditData({});

  const columns: any = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 96
    },
    {
      title: intl.get('graphList.knoNetworkname'),
      dataIndex: 'knw_name',
      width: 308,
      render: (text: string, record: any) => {
        const { id = '', color = '', knw_description = '' } = record;
        return (
          <div className="columnKnwName" onClick={() => onToPageNetwork(id)}>
            <AvatarName
              str={text}
              style={{
                color: `${color}`,
                background: `${`${color}15`}`,
                border: `1px solid ${`${color}10`}`
              }}
            />
            <div className="name-text" title={text}>
              <div className="name ad-ellipsis">{text}</div>
              {knw_description ? (
                <div className="des  ad-ellipsis">{knw_description}</div>
              ) : (
                <div className="des-null">{intl.get('graphList.notDes')}</div>
              )}
            </div>
          </div>
        );
      }
    },
    {
      title: intl.get('graphList.creationTime'),
      dataIndex: 'creation_time',
      width: 220,
      sorter: true,
      sortDirections: ['ascend', 'descend', 'ascend']
    },
    {
      title: intl.get('graphList.finalOperatorTime'),
      dataIndex: 'update_time',
      width: 220,
      sorter: true,
      defaultSortOrder: 'descend',
      sortDirections: ['ascend', 'descend', 'ascend']
    },
    {
      title: intl.get('graphList.operation'),
      dataIndex: 'op',
      width: 110,
      fixed: 'right',
      render: (text: string, record: any) => {
        return (
          <div className="ad-center columnOp" style={{ justifyContent: 'flex-start' }}>
            <Button type="link" onClick={() => onOpenCreateOrEdit(record)}>
              {intl.get('graphList.edit')}
            </Button>
            <Button type="link" onClick={() => onOpenDelete(record)}>
              {intl.get('graphList.delete')}
            </Button>
          </div>
        );
      }
    }
  ];

  return (
    <div id="netWork" className="netWork">
      <div className="ad-p-6 ad-bg-white" style={{ height: '100%' }}>
        <Format.Title className="ad-mb-5">{intl.get('graphList.mygraph')}</Format.Title>
        <div className="netWork-list">
          <div className="netWork-list-top">
            <Button type="primary" onClick={() => onOpenCreateOrEdit({})}>
              <IconFont type="icon-Add" style={{ color: '#fff' }} />
              {intl.get('graphList.create')}
            </Button>
            <SearchInput
              placeholder={intl.get('graphList.searchName')}
              onChange={searchChange}
              onPressEnter={(e: any) => onSearch(e?.target?.value)}
              onClear={() => onSearch('')}
            />
          </div>
          <div className="table-box">
            <Table
              columns={columns}
              scroll={{ x: '100%' }}
              dataSource={tableData}
              onChange={sortOrderChange}
              rowKey={(record: any) => record.id}
              loading={loading ? { indicator } : false}
              onRow={record => ({ onClick: () => setSelectKey(record.id) })}
              rowClassName={(record: any) => (record?.id === selectKey ? 'selectRow' : '')}
              pagination={{
                total,
                current: page,
                pageSize: size,
                showTitle: false,
                showSizeChanger: false,
                onChange: currentChange,
                showTotal: total => intl.get('graphList.total', { total })
              }}
              locale={{
                emptyText: !searchValue ? (
                  <div className="nodata-box">
                    <img src={addContentImg} alt="nodata" />
                    <div className="nodata-text">
                      <span>{intl.get('graphList.click')}</span>
                      <span className="create-span" onClick={() => onOpenCreateOrEdit({})}>
                        {intl.get('global.emptyTableCreate')}
                      </span>
                      <span>{intl.get('graphList.addNetwork')}</span>
                    </div>
                  </div>
                ) : (
                  <div className="nodata-box">
                    <img src={NoResult} alt="nodata" />
                    <div className="nodata-text">{intl.get('memberManage.searchNull')}</div>
                  </div>
                )
              }}
            />
          </div>
        </div>

        <CreateModal
          visible={!_.isEmpty(createOrEditData)}
          source={createOrEditData}
          onRefreshList={onRefreshList}
          onCloseCreateOrEdit={onCloseCreateOrEdit}
        />

        <DeleteModal visible={!!delId} delId={delId} onCloseDelete={onCloseDelete} onRefreshList={onRefreshList} />
      </div>
    </div>
  );
};

export default GraphList;
